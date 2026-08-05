import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'campaign-studio',
      component: () => import('@/views/CampaignStudioView.vue'),
    },
  ],
})

export default router
