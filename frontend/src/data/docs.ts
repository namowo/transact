export interface DocPage {
  slug: string
  title: string
  body: string
}

export const defaultDocSlug = 'introduction'

export const docPages: DocPage[] = [
  {
    slug: defaultDocSlug,
    title: 'Introduction',
    body: "TransAct helps laboratories track samples, methods, and recovery workflows in one place. Sign in to access your laboratory's dashboard, or browse these docs to learn more before creating an account.",
  },
  {
    slug: 'getting-started',
    title: 'Getting Started',
    body: 'Register an account for your laboratory, verify your email address from the link we send you, then sign in to start recording activities.',
  },
  {
    slug: 'faq',
    title: 'FAQ',
    body: 'Frequently asked questions will appear here.',
  },
]

export const fallbackDocPage: DocPage = docPages[0]!
