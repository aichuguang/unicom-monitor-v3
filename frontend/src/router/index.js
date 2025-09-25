import { createRouter, createWebHashHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { House, Setting, User, Document } from '@/utils/icons'

// 路由组件
const HomePage = () => import('@/views/HomePage.vue')
const ConfigPage = () => import('@/views/ConfigPage.vue')
const ProfilePage = () => import('@/views/ProfilePage.vue')
const HelpPage = () => import('@/views/HelpPage.vue')
const LoginPage = () => import('@/views/LoginPage.vue')
const RegisterPage = () => import('@/views/RegisterPage.vue')


const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage,
    meta: {
      title: '首页',
      requiresAuth: true,
      icon: House
    }
  },

  {
    path: '/config',
    name: 'Config',
    component: ConfigPage,
    meta: {
      title: '配置页',
      requiresAuth: true,
      icon: Setting
    }
  },

  {
    path: '/profile',
    name: 'Profile',
    component: ProfilePage,
    meta: {
      title: '个人中心',
      requiresAuth: true,
      icon: User
    }
  },
  {
    path: '/help',
    name: 'Help',
    component: HelpPage,
    meta: {
      title: '使用说明',
      requiresAuth: true,
      icon: Document
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: {
      title: '登录',
      requiresAuth: false,
      hideInMenu: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterPage,
    meta: {
      title: '注册',
      requiresAuth: false,
      hideInMenu: true
    }
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 联通流量监控系统` : '联通流量监控系统'

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      // 未登录，跳转到登录页
      next({
        name: 'Login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin && !userStore.isAdmin) {
      ElMessage.error('权限不足')
      next({ name: 'Home' })
      return
    }
  } else {
    // 不需要认证的页面，如果已登录则跳转到首页
    if (userStore.isLoggedIn && (to.name === 'Login' || to.name === 'Register')) {
      next({ name: 'Home' })
      return
    }
  }

  next()
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('页面加载失败，请刷新重试')
})

export default router

// 导出菜单路由（用于导航菜单）
export const menuRoutes = routes.filter(route =>
  !route.meta?.hideInMenu && route.meta?.requiresAuth
)
