import { createRouter, createWebHistory } from 'vue-router'

import CustomerList from '../views/CustomerList.vue'
import Dashboard from '../views/Dashboard.vue'
import DesignOptions from '../views/DesignOptions.vue'
import DesignTasks from '../views/DesignTasks.vue'
import AfterSalesRequests from '../views/AfterSalesRequests.vue'
import InvoiceRequests from '../views/InvoiceRequests.vue'
import Login from '../views/Login.vue'
import NewOrder from '../views/NewOrder.vue'
import OrderDetail from '../views/OrderDetail.vue'
import OrderList from '../views/OrderList.vue'
import ProductionArrangements from '../views/ProductionArrangements.vue'
import StoreList from '../views/StoreList.vue'
import SystemManagement from '../views/SystemManagement.vue'
import { useAuthStore } from '../stores/auth'

const systemPermissions = [
  'stores.change_store',
  'orders.change_designoption',
  'system_settings.change_paymentchannel',
  'system_settings.change_invoicetypeoption',
  'auth.view_user',
  'auth.view_group'
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/', component: Dashboard },
    { path: '/kanban', redirect: '/' },
    { path: '/orders', component: OrderList, meta: { permissions: ['orders.view_order'] } },
    { path: '/orders/new', component: NewOrder, meta: { permissions: ['orders.add_order'] } },
    { path: '/orders/:id', component: OrderDetail, meta: { permissions: ['orders.view_order'] } },
    { path: '/design-tasks', component: DesignTasks, meta: { permissions: ['design.view_designtask'] } },
    { path: '/production-arrangements', component: ProductionArrangements, meta: { permissions: ['production.view_productionarrangement'] } },
    { path: '/invoice-requests', component: InvoiceRequests, meta: { permissions: ['finance.view_invoicerequest'] } },
    { path: '/after-sales-requests', component: AfterSalesRequests, meta: { permissions: ['after_sales.view_aftersalesrequest'] } },
    { path: '/customers', component: CustomerList, meta: { permissions: ['customers.view_customer'] } },
    { path: '/system', component: SystemManagement, meta: { permissions: systemPermissions } },
    { path: '/stores', component: StoreList, meta: { permissions: ['stores.change_store'] } },
    { path: '/design-options', component: DesignOptions, meta: { permissions: ['orders.change_designoption'] } },
    { path: '/users', redirect: '/system' }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true

  if (!auth.user) {
    await auth.loadMe()
  }
  if (!auth.user) {
    return { path: '/login' }
  }

  const permissions = to.meta.permissions as string[] | undefined
  if (permissions?.length && !auth.hasAnyPermission(permissions)) {
    return { path: '/' }
  }
  return true
})

export default router
