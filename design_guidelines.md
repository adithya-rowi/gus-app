# Gus Ahab - Islamic Q&A Chatbot Design Guidelines

## Design Approach
**Reference-Based**: Drawing from WhatsApp's familiar chat patterns, Calm's spiritual warmth, and Islamic app conventions (Muslim Pro) to create a trustworthy, culturally-appropriate mobile experience.

## Core Design Principles
- **Warmth over sterility**: Soft edges, gentle shadows, human-centered design
- **Humble simplicity**: No flashy elements; focus on content and connection
- **Screenshot-optimized**: Every chat response should look beautiful when shared on Instagram
- **Mobile-native**: Touch-friendly, thumb-zone optimized, vertical-first

---

## Typography System
**Primary Font**: Plus Jakarta Sans (via Google Fonts CDN)
- Soft, friendly letterforms that feel approachable
- Excellent Indonesian language support

**Hierarchy**:
- App Title/Branding: text-2xl font-semibold
- Section Headers: text-lg font-medium
- Chat Messages: text-base (user) / text-base font-normal (Gus Ahab)
- Timestamps/Metadata: text-xs text-stone-500
- Donation CTAs: text-sm font-medium

---

## Layout System
**Spacing Primitives**: Tailwind units 2, 3, 4, 6, 8 (extremely consistent, simple rhythm)
- Component padding: p-4
- Section spacing: space-y-4
- Button padding: px-6 py-3
- Card/bubble spacing: p-3

**Container Strategy**:
- Chat container: max-w-2xl mx-auto (optimal reading width on larger screens)
- Full-width on mobile: w-full px-4
- Bottom fixed elements: fixed bottom-0 inset-x-0

---

## Component Library

### Navigation Header
- Sticky top bar (h-14) with soft shadow
- Left: Profile avatar of "Gus Ahab" (warmth/personality)
- Center: "Gus Ahab" title with subtle tagline below
- Right: Share to Instagram icon (always accessible)

### Chat Interface
**Message Bubbles**:
- User messages: Align right, amber-100 background, rounded-2xl rounded-tr-sm
- Gus Ahab responses: Align left, stone-100 background, rounded-2xl rounded-tl-sm
- Max width: max-w-[80%] for natural reading
- Padding: p-3, generous tap targets
- Shadow: Very subtle (shadow-sm) for depth

**Timestamp**: Below each message, text-xs, muted stone-500

**Input Area**:
- Fixed bottom with safe-area padding
- Elevated (shadow-lg) stone-white background
- Rounded text input with stone-200 border
- Send button: Amber accent with icon (Heroicons paper-airplane)

### Donation Prompts
**Natural Integration** (appears every 3-5 exchanges):
- Soft stone-50 background card between messages
- Gratitude-first language: "Jika terbantu, sedekah jariyah kami..." 
- Amber CTA button: "Donasi via Saweria"
- Dismissible with small "x" (non-intrusive)

### Share Components
**Instagram Share Button**:
- Floating action button (bottom-right, above input)
- Amber-500 background with Instagram icon
- Blurred backdrop (backdrop-blur-sm) if over content
- Tap reveals: "Screenshot & Share to Instagram Stories"

**Screenshot Optimization**:
- Auto-add subtle watermark "GusAhab.com" in footer of shared content
- Clean, distraction-free message display mode when sharing

### Empty States
- Initial greeting from Gus Ahab with warm illustration placeholder
- Suggested questions (3-4 common topics) as tappable chips
- Amber-50 background chips with stone-700 text

---

## Images
**No Large Hero Image** - This is a functional chat app where content is king.

**Avatar/Branding**:
- Small circular avatar (48px) of traditional Islamic scholar aesthetic (warm, approachable illustration)
- Used in header and as message sender indicator

**Suggested Question Icons** (via Heroicons):
- Simple line icons accompanying starter question chips
- Examples: book-open, heart, light-bulb

---

## Interactions
**Minimal Animations**:
- Message send: Gentle slide-up fade-in (150ms)
- New message arrival: Soft fade-in from left
- Donation prompt: Subtle scale-in when appears

**No hover states** (mobile-first) - Focus on touch feedback:
- Active button states: Slight scale(0.98) on press
- Ripple effect on message bubbles (optional via JavaScript)

---

## Accessibility
- Minimum 44px touch targets for all interactive elements
- High contrast text (stone-900 on light, stone-100 on dark)
- Semantic HTML with proper ARIA labels for screen readers
- Focus indicators for keyboard navigation (amber ring)

---

## Special Considerations
**Cultural Appropriateness**:
- Right-to-left consideration for Arabic text snippets
- Islamic greeting conventions ("Assalamualaikum" in initial message)
- Respect for spiritual context in all microcopy

**Monetization Integration**:
- Donation prompts feel like gratitude, not transactions
- Saweria link opens in new tab, returns to chat seamlessly
- Track donations via session (show thank-you message on return)

---

This design creates a warm, trustworthy spiritual companion that feels personal, shareable, and culturally authentic while maintaining simplicity and focus on meaningful conversation.