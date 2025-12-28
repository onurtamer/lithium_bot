from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken, SocialAccount
from lithium_core.models import (
    User as BotUser, Guild, OAuthSession, AutoModRule, 
    ModerationConfig, WelcomeConfig, LevelingConfig, TicketConfig,
    QuarantineConfig, EmbedConfig, StarboardConfig, AutoResponder,
    StickyMessage, AFKState, VoiceConfig, ReactionRoleMenu,
    LogRoute, ScheduledMessage, CustomCommand
)
from lithium_core.utils.permissions import define_role
from lithium_core.utils.audit import log_audit_sync
from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session
import requests
import os
import json
import redis
from django.http import JsonResponse, HttpResponse

# Database Setup
RAW_DB_URL = os.getenv("DATABASE_URL").replace("+asyncpg", "")
engine = create_engine(RAW_DB_URL)

def health_check(request):
    return JsonResponse({"status": "ok"})

def get_user_guilds(access_token):
    res = requests.get("https://discord.com/api/users/@me/guilds", headers={
        "Authorization": f"Bearer {access_token}"
    })
    return res.json() if res.status_code == 200 else []

@login_required
def dashboard_index(request):
    try:
        token_obj = SocialToken.objects.get(account__user=request.user, account__provider='discord')
        token = token_obj.token
    except SocialToken.DoesNotExist:
        return redirect('account_login')

    guilds = get_user_guilds(token)
    
    # Filter for Manage Guild (0x20)
    manage_guilds = []
    for g in guilds:
        if (int(g.get('permissions', 0)) & 0x20) == 0x20 or g.get('owner'):
            manage_guilds.append(g)
            
    return render(request, 'web/dashboard.html', {'guilds': manage_guilds})

@login_required
def guild_detail(request, guild_id):
    try:
        # Get Token and Discord ID
        token_obj = SocialToken.objects.get(account__user=request.user, account__provider='discord')
        social_acc = SocialAccount.objects.get(user=request.user, provider='discord')
        
        token = token_obj.token
        discord_id = social_acc.uid
    except (SocialToken.DoesNotExist, SocialAccount.DoesNotExist):
        return redirect('account_login')

    # Fetch Guilds to validate access and get name
    guilds = get_user_guilds(token)
    target_guild = next((g for g in guilds if g['id'] == guild_id), None)
    
    if not target_guild:
        return redirect('dashboard')
        
    role = define_role(target_guild, discord_id)
    if role == "VIEWER":
        pass 

    with Session(engine) as session:
        if request.method == "POST":
            if role not in ["OWNER", "ADMIN", "MODERATOR"]:
                return render(request, 'web/partials/rules_list.html', {'error': 'Permission Denied'})

            # Handle Form Submit
            new_rule = AutoModRule(
                guild_id=guild_id,
                rule_type="BAD_WORDS",
                config={"words": request.POST.get('words', '').split(',')},
                actions={"type": "DELETE"},
                enabled=True
            )
            session.add(new_rule)
            session.commit()
            
            # Log Audit
            log_audit_sync(
                guild_id=guild_id,
                user_id=discord_id,
                action="CREATE_RULE",
                target="automod",
                changes={"type": "BAD_WORDS", "config": new_rule.config}
            )
            
            # Publish to Redis
            r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
            r.publish("guild_config_changed", json.dumps({
                "guild_id": guild_id,
                "module": "automod",
                "action": "create"
            }))
            
            # HTMX Response
            stmt = select(AutoModRule).where(AutoModRule.guild_id == guild_id)
            rules = session.execute(stmt).scalars().all()
            return render(request, 'web/partials/rules_list.html', {'rules': rules})

        # GET Request
        stmt = select(AutoModRule).where(AutoModRule.guild_id == guild_id)
        rules = session.execute(stmt).scalars().all()

    return render(request, 'web/guild_detail.html', {
        'guild_id': guild_id, 
        'rules': rules,
        'role': role,
        'guild_name': target_guild['name'],
        'guild': target_guild # Passing dict from API
    })

@login_required
def module_config(request, guild_id, module_name):
    # Authorization and Guild Validation (similar to guild_detail)
    try:
        token_obj = SocialToken.objects.get(account__user=request.user, account__provider='discord')
        social_acc = SocialAccount.objects.get(user=request.user, provider='discord')
        token = token_obj.token
        discord_id = social_acc.uid
    except (SocialToken.DoesNotExist, SocialAccount.DoesNotExist):
        return redirect('account_login')

    guilds = get_user_guilds(token)
    target_guild = next((g for g in guilds if g['id'] == guild_id), None)
    if not target_guild:
        return redirect('dashboard')

    role = define_role(target_guild, discord_id)
    
    # Module specific logic
    template_name = f'web/modules/{module_name}.html'
    context = {
        'guild_id': guild_id,
        'guild_name': target_guild['name'],
        'role': role,
        'module_name': module_name
    }

    if request.method == "POST":
        if role not in ["OWNER", "ADMIN"]: # Strict for settings
            return HttpResponse(status=403)
            
        with Session(engine) as session:
            if module_name == "moderation":
                stmt = select(ModerationConfig).where(ModerationConfig.guild_id == guild_id)
                config = session.execute(stmt).scalar_one_or_none()
                if not config:
                    config = ModerationConfig(guild_id=guild_id)
                    session.add(config)
                
                config.log_channel_id = request.POST.get('log_channel_id')
                session.commit()
            elif module_name == "starboard":
                stmt = select(StarboardConfig).where(StarboardConfig.guild_id == guild_id)
                config = session.execute(stmt).scalar_one_or_none()
                if not config:
                    config = StarboardConfig(guild_id=guild_id)
                    session.add(config)
                
                config.channel_id = request.POST.get('channel_id')
                config.threshold = int(request.POST.get('threshold', 3))
                config.emoji = request.POST.get('emoji', '⭐')
                session.commit()
            elif module_name == "anti-raid":
                stmt = select(QuarantineConfig).where(QuarantineConfig.guild_id == guild_id)
                config = session.execute(stmt).scalar_one_or_none()
                if not config:
                    config = QuarantineConfig(guild_id=guild_id)
                    session.add(config)
                
                config.max_joins_per_minute = int(request.POST.get('max_joins', 10))
                config.min_account_age_days = int(request.POST.get('min_age', 0))
                config.require_avatar = request.POST.get('require_avatar') == 'on'
                config.action = request.POST.get('action', 'KICK')
                session.commit()
            elif module_name == "leveling":
                stmt = select(LevelingConfig).where(LevelingConfig.guild_id == guild_id)
                config = session.execute(stmt).scalar_one_or_none()
                if not config:
                    config = LevelingConfig(guild_id=guild_id)
                    session.add(config)
                
                config.min_xp = int(request.POST.get('min_xp', 15))
                config.max_xp = int(request.POST.get('max_xp', 25))
                session.commit()
            elif module_name == "tickets":
                stmt = select(TicketConfig).where(TicketConfig.guild_id == guild_id)
                config = session.execute(stmt).scalar_one_or_none()
                if not config:
                    config = TicketConfig(guild_id=guild_id)
                    session.add(config)
                
                config.category_id = request.POST.get('category_id')
                config.support_role_id = request.POST.get('support_role_id')
                session.commit()
            # Add more modules as needed
            
            # Redis Notify
            r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
            r.publish("guild_config_changed", json.dumps({
                "guild_id": guild_id,
                "module": module_name,
                "action": "update"
            }))

            if request.headers.get('HX-Request'):
                return render(request, 'web/partials/toast.html', {
                    'message': f'{module_name.replace("-", " ").capitalize()} settings updated successfully!',
                    'type': 'success'
                })

    with Session(engine) as session:
        # Fetch guild from DB to check toggles
        db_guild = session.get(Guild, guild_id)
        if not db_guild:
            # If not in DB, create it
            db_guild = Guild(id=guild_id, name=target_guild['name'], owner_id=target_guild['owner_id'] if 'owner_id' in target_guild else discord_id)
            session.add(db_guild)
            session.commit()
        
        context['db_guild'] = db_guild

        # Add module specific data to context
        if module_name == "overview":
            # Summary stats
            context['module_stats'] = {
                'enabled_count': sum(1 for field in db_guild.__table__.columns if field.name.endswith('_enabled') and getattr(db_guild, field.name)),
                'total_count': sum(1 for field in db_guild.__table__.columns if field.name.endswith('_enabled')),
            }
        if module_name == "test-configuration":
            # Call the diagnostic engine
            context['bot_status'] = run_guild_diagnostics(guild_id)
            if request.headers.get('HX-Request') and request.method == "POST":
                return render(request, 'web/partials/diagnostic_results.html', context)
        elif module_name == "audit":
            # For now dummy, would fetch QuarantineLog or a new AuditLog model
            context['audit_logs'] = []
            
        elif module_name == "automod":
            stmt = select(AutoModRule).where(AutoModRule.guild_id == guild_id)
            context['rules'] = session.execute(stmt).scalars().all()
        elif module_name == "moderation":
            stmt = select(ModerationConfig).where(ModerationConfig.guild_id == guild_id)
            config = session.execute(stmt).scalar_one_or_none()
            context['config'] = config
        # ... add more as needed

    return render(request, template_name, context)

@login_required
def toggle_module(request, guild_id, module_name):
    if request.method != "POST":
        return HttpResponse(status=405)

    # Permission check for ADMIN/OWNER usually for toggles
    # Simplified for now
    
    with Session(engine) as session:
        guild = session.get(Guild, guild_id)
        if not guild:
            return JsonResponse({"error": "Guild not found"}, status=404)
        
        field_name = f"{module_name}_enabled"
        if hasattr(guild, field_name):
            current_val = getattr(guild, field_name)
            setattr(guild, field_name, not current_val)
            session.commit()
            
            # Redis Notify
            r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
            r.publish("guild_config_changed", json.dumps({
                "guild_id": guild_id,
                "module": module_name,
                "action": "toggle",
                "enabled": not current_val
            }))
            
            if request.headers.get('HX-Request'):
                return render(request, 'web/partials/toast.html', {
                    'message': f'{module_name.replace("-", " ").capitalize()} module {"enabled" if not current_val else "disabled"}!',
                    'type': 'success'
                })
            
            return JsonResponse({"enabled": not current_val})
        
    return JsonResponse({"error": "Invalid module"}, status=400)
