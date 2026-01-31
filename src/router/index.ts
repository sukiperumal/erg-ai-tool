import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue')
  },
    {
      path: '/courses/1',
      name: 'criminal-law',
      component: () => import('@/views/courses/CriminalLaw.vue'),
    },
    { 
      path: '/courses/2',
      name: 'stroke-analysis',
      component: () => import('@/views/courses/StrokeAnalysis.vue'),
    },
    {
      path: '/courses/3',
      name: 'environment-cba',
      component: () => import('@/views/courses/Environment.vue'),
    },
    {
      path: '/courses/1/cohorts/1',
      name: 'criminal-law-cohort-1',
      component: () => import('@/views/courses/cohorts/CL1.vue'),
    },
    {
      path: '/courses/1/cohorts/2',
      name: 'criminal-law-cohort-2',
      component: () => import('@/views/courses/cohorts/CL2.vue'),  
    },
    {
      path: '/courses/1/cohorts/3',
      name: 'criminal-law-cohort-3',
      component: () => import('@/views/courses/cohorts/CL3.vue'),  
    },
    {
      path: '/courses/2/cohorts/1',
      name: 'stroke-analysis-cohort-1',
      component: () => import('@/views/courses/cohorts/SA1.vue'),
    },
    {
      path: '/courses/2/cohorts/2',
      name: 'stroke-analysis-cohort-2',
      component: () => import('@/views/courses/cohorts/SA2.vue'),  
    },
    {
      path: '/courses/2/cohorts/3',
      name: 'stroke-analysis-cohort-3',
      component: () => import('@/views/courses/cohorts/SA3.vue'),  
    },
    {
      path: '/courses/3/cohorts/1',
      name: 'environment-cba-cohort-1',
      component: () => import('@/views/courses/cohorts/CBA1.vue'),
    },
    {
      path: '/courses/3/cohorts/2',
      name: 'environment-cba-cohort-2',
      component: () => import('@/views/courses/cohorts/CBA2.vue'),  
    },
    {
      path: '/courses/3/cohorts/3',
      name: 'environment-cba-cohort-3',
      component: () => import('@/views/courses/cohorts/CBA3.vue'),  
    },
  ],
})

export default router
