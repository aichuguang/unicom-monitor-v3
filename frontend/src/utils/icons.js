// 使用 Heroicons 替代 Element Plus Icons
// Heroicons 更稳定，兼容性更好

// 实心图标 (24x24)
import {
  HomeIcon,
  ComputerDesktopIcon,
  CogIcon,
  UserIcon,
  Bars3Icon,
  ChevronDownIcon,
  WrenchScrewdriverIcon,
  ArrowRightOnRectangleIcon,
  SunIcon,
  MoonIcon,
  ArrowPathIcon,
  ArrowUturnLeftIcon,
  PlusIcon,
  CheckIcon,
  XMarkIcon,
  PhoneIcon,
  DocumentIcon,
  ExclamationTriangleIcon,
  LockClosedIcon,
  EnvelopeIcon,
  UserCircleIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  EyeIcon,
  DevicePhoneMobileIcon,
  EllipsisVerticalIcon,
  ClockIcon,
  ChartBarIcon,
  PresentationChartLineIcon,
  TrashIcon
} from '@heroicons/vue/24/solid'

// 统一导出，使用语义化的名称
export {
  // 基础图标
  HomeIcon as House,
  ComputerDesktopIcon as Monitor,
  CogIcon as Setting,
  UserIcon as User,
  Bars3Icon as Menu,
  ChevronDownIcon as ArrowDown,

  // 操作图标
  ArrowPathIcon as Refresh,
  ArrowUturnLeftIcon as RefreshLeft,
  PlusIcon as Plus,
  CheckIcon as Check,
  ArrowPathIcon as Loading, // 使用旋转箭头作为加载图标
  XMarkIcon as Close,
  TrashIcon as Delete,

  // 状态图标
  PhoneIcon as Phone,
  DocumentIcon as Document,
  ExclamationTriangleIcon as Warning,

  // 表单图标
  LockClosedIcon as Lock,
  EnvelopeIcon as Message,
  UserCircleIcon as Avatar,

  // 通知图标
  CheckCircleIcon as SuccessFilled,
  ExclamationTriangleIcon as WarningFilled,
  ExclamationCircleIcon as CircleCloseFilled,
  InformationCircleIcon as InfoFilled,

  // 用户图标
  UserCircleIcon as UserFilled,

  // 系统图标
  WrenchScrewdriverIcon as Tools,
  ArrowRightOnRectangleIcon as SwitchButton,
  SunIcon as Sunny,
  MoonIcon as Moon,

  // 布局图标
  ChevronLeftIcon as Fold,
  ChevronRightIcon as Expand,
  EyeIcon as View,

  // 移动端图标
  DevicePhoneMobileIcon as Iphone,

  // 更多操作图标
  EllipsisVerticalIcon as MoreFilled,

  // 时间图标
  ClockIcon,

  // 数据分析图标
  ChartBarIcon as DataAnalysis,
  PresentationChartLineIcon as Chart
}

// 图标映射表，用于动态获取图标
export const iconMap = {
  House: HomeIcon,
  Monitor: ComputerDesktopIcon,
  Setting: CogIcon,
  User: UserIcon,
  Menu: Bars3Icon,
  ArrowDown: ChevronDownIcon,
  Refresh: ArrowPathIcon,
  RefreshLeft: ArrowUturnLeftIcon,
  Plus: PlusIcon,
  Check: CheckIcon,
  Loading: ArrowPathIcon,
  Close: XMarkIcon,
  Delete: TrashIcon,
  Phone: PhoneIcon,
  Document: DocumentIcon,
  Warning: ExclamationTriangleIcon,
  Lock: LockClosedIcon,
  Message: EnvelopeIcon,
  Avatar: UserCircleIcon,
  SuccessFilled: CheckCircleIcon,
  WarningFilled: ExclamationTriangleIcon,
  CircleCloseFilled: ExclamationCircleIcon,
  InfoFilled: InformationCircleIcon,
  UserFilled: UserCircleIcon,
  Tools: WrenchScrewdriverIcon,
  SwitchButton: ArrowRightOnRectangleIcon,
  Sunny: SunIcon,
  Moon: MoonIcon,
  Fold: ChevronLeftIcon,
  Expand: ChevronRightIcon,
  View: EyeIcon,
  Iphone: DevicePhoneMobileIcon,
  MoreFilled: EllipsisVerticalIcon
}

// 获取图标组件的辅助函数
export const getIcon = (iconName) => {
  return iconMap[iconName] || DocumentIcon
}
