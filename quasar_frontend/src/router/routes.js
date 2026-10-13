
const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/filtered' },
      { path: '/old', component: () => import('pages/IndexPage_availibility_expand.vue') },
      { path: '/scheduled', component: () => import('pages/ScheduledMonitoring.vue') },
      // { path: '/paping', component: () => import('pages/PapingMonitoring.vue') },
      { path: '/whitelist', component: () => import('pages/WhitelistManagement.vue') },
      { path: '/filtered', component: () => import('pages/FilteredResults.vue') },
    ]
  },


  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
