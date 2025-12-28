import pytest
from lithium_core.utils.permissions import define_role

class TestPermissions:
    def test_owner_role(self):
        guild = {'owner_id': '123', 'name': 'Test Guild'}
        assert define_role(guild, '123') == "OWNER"
        
    def test_admin_role(self):
        # 0x8 is admin
        guild = {'owner_id': '999', 'permissions': 8}
        assert define_role(guild, '123') == "ADMIN"
        
    def test_moderator_role(self):
        # 0x20 is manage guild
        guild = {'owner_id': '999', 'permissions': 32}
        assert define_role(guild, '123') == "MODERATOR"
        
    def test_viewer_role(self):
        guild = {'owner_id': '999', 'permissions': 0}
        assert define_role(guild, '123') == "VIEWER"
