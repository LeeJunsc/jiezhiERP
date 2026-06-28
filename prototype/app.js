const titles = {
  dashboard: "工作台",
  orders: "订单列表",
  "new-order": "新建订单",
  "order-detail": "订单详情",
  design: "设计任务",
  production: "生产安排",
  customers: "客户管理",
  invoice: "发票审批",
  payment: "付款申请",
  "after-sales": "售后申请",
  users: "用户权限"
};

const orders = [
  {
    no: "JZ20260628001",
    store: "淘宝旗舰店",
    customer: "陈女士",
    amount: "2680.00",
    status: "设计中",
    option: "新订单需要设计",
    design: "设计中",
    production: "未安排",
    delivery: "2026-07-05",
    owner: "李销售"
  },
  {
    no: "JZ20260628002",
    store: "抖音定制店",
    customer: "明辰贸易",
    amount: "8600.00",
    status: "待生产安排",
    option: "续订无需设计",
    design: "无需设计",
    production: "待安排",
    delivery: "2026-07-08",
    owner: "王销售"
  },
  {
    no: "JZ20260627018",
    store: "小红书买手店",
    customer: "周先生",
    amount: "1290.00",
    status: "待生产安排",
    option: "仅标注",
    design: "已确认",
    production: "已安排",
    delivery: "2026-07-02",
    owner: "李销售"
  },
  {
    no: "JZ20260626009",
    store: "淘宝旗舰店",
    customer: "星禾设计",
    amount: "4200.00",
    status: "已完成",
    option: "老订单修改",
    design: "已确认",
    production: "安排确认",
    delivery: "2026-06-30",
    owner: "赵销售"
  }
];

function statusTag(value) {
  const className = value.includes("完成") || value.includes("确认") ? "green" : value.includes("生产") ? "amber" : "blue";
  return `<span class="tag ${className}">${value}</span>`;
}

function renderOrders() {
  const recent = document.querySelector("#recent-orders");
  const table = document.querySelector("#orders-table");

  recent.innerHTML = orders
    .slice(0, 3)
    .map(
      (order) => `
        <tr>
          <td>${order.no}</td>
          <td>${order.store}</td>
          <td>${order.customer}</td>
          <td>${statusTag(order.status)}</td>
          <td>${order.delivery}</td>
          <td>${order.owner}</td>
        </tr>
      `
    )
    .join("");

  table.innerHTML = orders
    .map(
      (order) => `
        <tr>
          <td>${order.no}</td>
          <td>${order.store}</td>
          <td>${order.customer}</td>
          <td>${order.amount}</td>
          <td>${statusTag(order.status)}</td>
          <td>${order.option}</td>
          <td>${order.design}</td>
          <td>${order.production}</td>
          <td>${order.delivery}</td>
          <td><button class="small-btn" data-screen-link="order-detail">详情</button></td>
        </tr>
      `
    )
    .join("");
}

function showScreen(id) {
  document.querySelectorAll(".screen").forEach((screen) => {
    screen.classList.toggle("active", screen.id === id);
  });

  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.screen === id);
  });

  document.querySelector("#screen-title").textContent = titles[id] || "工作台";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.addEventListener("click", (event) => {
  const navTarget = event.target.closest("[data-screen], [data-screen-link]");
  if (!navTarget) return;

  const screenId = navTarget.dataset.screen || navTarget.dataset.screenLink;
  if (screenId && document.getElementById(screenId)) {
    showScreen(screenId);
  }
});

renderOrders();
