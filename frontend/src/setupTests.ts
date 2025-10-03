/**
 * Jest 测试环境设置
 * 配置测试所需的全局设置和模拟
 */

import '@testing-library/jest-dom'

// 模拟 ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// 模拟 IntersectionObserver
class MockIntersectionObserver {
  root: Element | null = null
  rootMargin: string = '0px'
  thresholds: ReadonlyArray<number> = []
  
  constructor(_callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.root = (options?.root as Element) || null
    this.rootMargin = options?.rootMargin || '0px'
    this.thresholds = options?.threshold ? (Array.isArray(options.threshold) ? options.threshold : [options.threshold]) : []
  }
  
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

(global as any).IntersectionObserver = MockIntersectionObserver

// 模拟 matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// 模拟 scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: jest.fn(),
})

// 模拟 localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// 模拟 sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// 模拟 fetch
global.fetch = jest.fn()

// 模拟 URL.createObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: jest.fn(() => 'mocked-url'),
})

// 模拟 URL.revokeObjectURL
Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: jest.fn(),
})

// 模拟 navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn(() => Promise.resolve()),
    readText: jest.fn(() => Promise.resolve('')),
  },
  writable: true,
})

// 模拟 File 构造函数
class MockFile {
  name: string
  size: number
  type: string
  lastModified: number
  webkitRelativePath: string = ''
  stream: () => ReadableStream = () => new ReadableStream()
  text: () => Promise<string> = () => Promise.resolve('')
  arrayBuffer: () => Promise<ArrayBuffer> = () => Promise.resolve(new ArrayBuffer(0))
  slice: (start?: number, end?: number, contentType?: string) => Blob = () => new Blob()

  constructor(fileBits: BlobPart[], fileName: string, options?: FilePropertyBag) {
    this.name = fileName
    this.size = fileBits.reduce((acc, bit) => acc + (typeof bit === 'string' ? bit.length : (bit as any).size || 0), 0)
    this.type = options?.type || ''
    this.lastModified = Date.now()
  }
}

(global as any).File = MockFile

// 模拟 FileReader
class MockFileReader {
  static readonly EMPTY = 0
  static readonly LOADING = 1
  static readonly DONE = 2
  
  readonly EMPTY = 0
  readonly LOADING = 1
  readonly DONE = 2
  
  result: string | ArrayBuffer | null = null
  error: any = null
  readyState: number = 0
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null
  onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null

  readAsText(_file: Blob) {
    this.readyState = 1
    setTimeout(() => {
      this.result = 'mocked file content'
      this.readyState = 2
      if (this.onload) {
        this.onload.call(this as any, {} as ProgressEvent<FileReader>)
      }
    }, 0)
  }

  readAsDataURL(_file: Blob) {
    this.readyState = 1
    setTimeout(() => {
      this.result = 'data:text/plain;base64,bW9ja2VkIGZpbGUgY29udGVudA=='
      this.readyState = 2
      if (this.onload) {
        this.onload.call(this as any, {} as ProgressEvent<FileReader>)
      }
    }, 0)
  }

  readAsArrayBuffer(_file: Blob) {
    this.readyState = 1
    setTimeout(() => {
      this.result = new ArrayBuffer(0)
      this.readyState = 2
      if (this.onload) {
        this.onload.call(this as any, {} as ProgressEvent<FileReader>)
      }
    }, 0)
  }

  readAsBinaryString(_file: Blob) {
    this.readyState = 1
    setTimeout(() => {
      this.result = 'binary string'
      this.readyState = 2
      if (this.onload) {
        this.onload.call(this as any, {} as ProgressEvent<FileReader>)
      }
    }, 0)
  }

  abort() {
    this.readyState = 2
    if (this.onabort) {
      this.onabort.call(this as any, {} as ProgressEvent<FileReader>)
    }
  }

  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true }
}

(global as any).FileReader = MockFileReader

// 模拟 console 方法（避免测试时的日志输出）
const originalError = console.error
const originalWarn = console.warn

beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return
    }
    originalError.call(console, ...args)
  }

  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('componentWillReceiveProps has been renamed')
    ) {
      return
    }
    originalWarn.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
  console.warn = originalWarn
})

// 清理函数
afterEach(() => {
  jest.clearAllMocks()
  localStorageMock.clear()
  sessionStorageMock.clear()
})

// 全局测试工具函数
;(global as any).createMockFile = (name: string, content: string, type: string = 'text/plain') => {
  return new File([content], name, { type })
}

;(global as any).createMockEvent = (type: string, properties: any = {}) => {
  const event = new Event(type)
  Object.assign(event, properties)
  return event
}

// 模拟 Zustand stores
jest.mock('@/stores/authStore', () => ({
  useAuthStore: jest.fn(() => ({
    isAuthenticated: false,
    user: null,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
  })),
  useAuth: jest.fn(() => ({
    isAuthenticated: false,
    user: null,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
  })),
}))

jest.mock('@/stores/themeStore', () => ({
  useThemeStore: jest.fn(() => ({
    theme: 'light',
    setTheme: jest.fn(),
    toggleTheme: jest.fn(),
  })),
}))

// 模拟 React Router
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({
    pathname: '/',
    search: '',
    hash: '',
    state: null,
  }),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
}))

// 模拟 Framer Motion
jest.mock('framer-motion', () => ({
  motion: {
    div: 'div',
    span: 'span',
    button: 'button',
    form: 'form',
    input: 'input',
    textarea: 'textarea',
    select: 'select',
    img: 'img',
    a: 'a',
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    h4: 'h4',
    h5: 'h5',
    h6: 'h6',
    p: 'p',
    ul: 'ul',
    ol: 'ol',
    li: 'li',
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
  useAnimation: () => ({
    start: jest.fn(),
    stop: jest.fn(),
    set: jest.fn(),
  }),
}))

// 模拟 Sonner toast
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  },
  Toaster: () => null,
}))

// 模拟 Lucide React 图标
jest.mock('lucide-react', () => {
  const React = require('react')
  const MockIcon = ({ className, ...props }: any) => {
    return React.createElement('svg', {
      className,
      ...props,
      'data-testid': 'mock-icon',
    })
  }
  
  return new Proxy({}, {
    get: () => MockIcon,
  })
})