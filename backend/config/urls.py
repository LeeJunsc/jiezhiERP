from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import RoleViewSet, UserViewSet, login_view, logout_view, me_view
from after_sales.views import AfterSalesRequestViewSet
from common.dashboard_views import dashboard_kanban, dashboard_summary
from attachments.views import AttachmentViewSet
from customers.views import CustomerViewSet
from design.views import DesignTaskViewSet
from finance.views import InvoiceRequestViewSet
from orders.views import DesignOptionViewSet, OrderViewSet
from production.views import ProductionArrangementViewSet
from stores.views import StoreViewSet
from system_settings.views import PaymentChannelViewSet


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("roles", RoleViewSet, basename="roles")
router.register("stores", StoreViewSet, basename="stores")
router.register("customers", CustomerViewSet, basename="customers")
router.register("design-options", DesignOptionViewSet, basename="design-options")
router.register("orders", OrderViewSet, basename="orders")
router.register("design-tasks", DesignTaskViewSet, basename="design-tasks")
router.register("production-arrangements", ProductionArrangementViewSet, basename="production-arrangements")
router.register("attachments", AttachmentViewSet, basename="attachments")
router.register("payment-channels", PaymentChannelViewSet, basename="payment-channels")
router.register("invoice-requests", InvoiceRequestViewSet, basename="invoice-requests")
router.register("after-sales-requests", AfterSalesRequestViewSet, basename="after-sales-requests")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/login", login_view, name="login"),
    path("api/v1/auth/logout", logout_view, name="logout"),
    path("api/v1/auth/me", me_view, name="me"),
    path("api/v1/dashboard/summary", dashboard_summary, name="dashboard-summary"),
    path("api/v1/dashboard/kanban", dashboard_kanban, name="dashboard-kanban"),
    path("api/v1/", include(router.urls)),
]
