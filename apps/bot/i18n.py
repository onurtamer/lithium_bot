STRINGS = {
    "en": {
        "user_banned": "✅ {user} has been banned.",
        "user_kicked": "✅ {user} has been kicked.",
        "perm_denied": "❌ You do not have permission to use this command.",
        "quarantine_active": "🔒 **GUILD QUARANTINE ACTIVE**. Filters are tightened.",
        "quarantine_lifted": "🔓 **GUILD QUARANTINE LIFTED**.",
        "user_softbanned": "✅ {user} has been softbanned.",
    },
    "tr": {
        "user_banned": "✅ {user} yasaklandı.",
        "user_kicked": "✅ {user} atıldı.",
        "perm_denied": "❌ Bu komutu kullanmak için yetkiniz yok.",
        "quarantine_active": "🔒 **SUNUCU KARANTİNASI AKTİF**. Filtreler sıkılaştırıldı.",
        "quarantine_lifted": "🔓 **SUNUCU KARANTİNASI KALDIRILDI**.",
        "user_softbanned": "✅ {user} sessizce yasaklandı ve atıldı.",
    }
}

def translate(key: str, lang: str = "en", **kwargs) -> str:
    lang_batch = STRINGS.get(lang.lower(), STRINGS["en"])
    tpl = lang_batch.get(key, STRINGS["en"].get(key, key))
    return tpl.format(**kwargs)
