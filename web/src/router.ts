import { createRouter, createWebHashHistory } from 'vue-router'

/**
 * 使用 hash 路由：静态部署友好，且不会与 `?data=` 查询参数（位于 hash 之前）冲突。
 */
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'overview',
      component: () => import('@/views/OverviewView.vue')
    },
    {
      path: '/blueprints',
      name: 'blueprints',
      component: () => import('@/views/BlueprintsView.vue')
    },
    {
      path: '/blueprints/:id',
      name: 'blueprint-detail',
      component: () => import('@/views/BlueprintDetailView.vue'),
      props: true
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router
