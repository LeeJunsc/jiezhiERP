import { createRouter, createWebHistory } from 'vue-router'

import CustomerList from '../views/CustomerList.vue'
import Dashboard from '../views/Dashboard.vue'
import DesignOptions from '../views/DesignOptions.vue'
import DesignTasks from '../views/DesignTasks.vue'
import Kanban from '../views/Kanban.vue'
import AfterSalesRequests from '../views/AfterSalesRequests.vue'
import InvoiceRequests from '../views/InvoiceRequests.vue'
import Login from '../views/Login.vue'
import NewOrder from '../views/NewOrder.vue'
import OrderDetail from '../views/OrderDetail.vue'
import OrderList from '../views/OrderList.vue'
import ProductionArrangements from '../views/ProductionArrangements.vue'
import StoreList from '../views/StoreList.vue'
import SystemManagement from '../views/SystemManagement.vue'
import UserList from '../views/UserList.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    { path: '/', component: Dashboard },
    { path: '/kanban', component: Kanban },
    { path: '/orders', component: OrderList },
    { path: '/orders/new', component: NewOrder },
    { path: '/orders/:id', component: OrderDetail },
    { path: '/design-tasks', component: DesignTasks },
    { path: '/production-arrangements', component: ProductionArrangements },
    { path: '/invoice-requests', component: InvoiceRequests },
    { path: '/after-sales-requests', component: AfterSalesRequests },
    { path: '/customers', component: CustomerList },
    { path: '/system', component: SystemManagement },
    { path: '/stores', component: StoreList },
    { path: '/design-options', component: DesignOptions },
    { path: '/users', component: UserList }
  ]
})

export default router
