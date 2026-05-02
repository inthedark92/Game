from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView
from . import views
from . import combat_api
from . import api_views

urlpatterns = [
    # API v2 (DRF)
    path('api/v2/auth/login/', api_views.LoginView.as_view(), name='api_login'),
    path('api/v2/auth/register/', api_views.RegisterView.as_view(), name='api_register'),
    path('api/v2/auth/logout/', api_views.LogoutView.as_view(), name='api_logout'),
    path('api/v2/auth/me/', api_views.MeView.as_view(), name='api_me'),
    path('api/v2/profile/distribute_stat/', api_views.DistributeStatView.as_view(), name='api_distribute_stat_v2'),
    path('api/v2/inventory/', api_views.InventoryListView.as_view(), name='api_inventory_v2'),
    path('api/v2/inventory/equip/', api_views.EquipItemView.as_view(), name='api_equip_v2'),
    path('api/v2/inventory/unequip/', api_views.UnequipItemView.as_view(), name='api_unequip_v2'),
    path('api/v2/inventory/use/', api_views.UseItemView.as_view(), name='api_use_v2'),
    path('api/v2/shop/', api_views.ShopListView.as_view(), name='api_shop_v2'),
    path('api/v2/shop/purchase/', api_views.ShopPurchaseView.as_view(), name='api_shop_purchase_v2'),
    path('api/v2/tavern/', api_views.TavernListView.as_view(), name='api_tavern_v2'),
    path('api/v2/tavern/purchase/', api_views.TavernPurchaseView.as_view(), name='api_tavern_purchase_v2'),
    path('api/v2/combat/hunt/', api_views.StartHuntView.as_view(), name='api_hunt_v2'),
    path('api/v2/combat/<uuid:combat_id>/state/', api_views.CombatStateView.as_view(), name='api_combat_state_v2'),
    path('api/v2/combat/<uuid:combat_id>/turn/', api_views.CombatTurnView.as_view(), name='api_combat_turn_v2'),

    # Основные URL
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('game/', views.game_home, name='game_home'),

    
    # Панели игры
    path('game/character/', views.character_panel, name='character_panel'),
    path('game/inventory/', views.inventory_panel, name='inventory_panel'),
    path('game/shop/', views.shop_panel, name='shop_panel'),
    path('game/tavern/', views.tavern_panel, name='tavern_panel'),
    path('game/arena/', views.arena_panel, name='arena_panel'),
    path('game/clan/', views.clan_panel, name='clan_panel'),
    path('game/bank/', views.bank_panel, name='bank_panel'),
    path('game/trade/', views.trade_panel, name='trade_panel'),
    
    # API endpoints
    path('api/inventory/', views.inventory_api, name='inventory_api'),
    path('api/inventory/item/<int:item_id>/', views.api_inventory_item_details, name='api_inventory_item_details'),
    path('api/inventory/equip/', views.equip_item, name='equip_item'),
    path('api/inventory/use/', views.api_use_item, name='api_use_item'),
    path('api/equipment/', views.api_equipment, name='api_equipment'),
    path('api/inventory/unequip/', views.unequip_item, name='unequip_item'),
    path('api/shop/items/', views.shop_items_api, name='shop_items_api'),
    path('api/shop/purchase/', views.api_shop_purchase, name='api_shop_purchase'),
    path('api/profile/distribute_stat/', views.api_distribute_stat, name='api_distribute_stat'),

    path('chat/get_messages/', views.get_messages, name='get_messages'),
    path('chat/send_message/', views.send_message, name='send_message'),
    path('tavern/menu/', views.tavern_menu_api, name='tavern_menu_api'),
    path('tavern/purchase/', views.tavern_purchase, name='tavern_purchase'),
    path('game/admin/authenticate/', views.admin_authenticate, name='admin_authenticate'),
    path('game/admin/', views.admin_panel, name='admin_panel'),
    path('game/admin/player/<int:player_id>/', views.admin_get_player_details, name='admin_get_player_details'),
    path('game/admin/ban/<int:player_id>/', views.admin_ban_player, name='admin_ban_player'),
    path('game/admin/get_admin_data/', views.admin_get_data, name='admin_get_data'),
    path('api/online_players/', views.online_players_api, name='online_players_api'),

    path('api/hunt/', combat_api.api_hunt, name='api_hunt'),
    path('api/combat/<uuid:combat_id>/turn/', combat_api.api_combat_turn, name='api_combat_turn'),
    path('api/combat/<uuid:combat_id>/state/', combat_api.api_combat_state, name='api_combat_state'),
]