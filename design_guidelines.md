# Design Guidelines for Gus App

## Design Approach: Reference-Based (Notion + Linear)
**Rationale**: AI-powered content generation tool requires clean, distraction-free interface with clear information hierarchy. Drawing from Notion's content focus and Linear's precise typography.

## Typography System
- **Primary Font**: Inter (Google Fonts) - excellent readability for interfaces
- **Monospace Font**: JetBrains Mono - for code/technical output
- **Hierarchy**:
  - Hero/Main: text-5xl font-bold
  - Section Headers: text-3xl font-semibold
  - Subsections: text-xl font-medium
  - Body: text-base
  - Labels/Meta: text-sm text-gray-600

## Layout System
**Spacing Primitives**: Use Tailwind units of 2, 4, 6, 8, 12, 16
- Component padding: p-6 or p-8
- Section spacing: space-y-8 or space-y-12
- Container max-width: max-w-6xl mx-auto
- Form elements: gap-6

## Core Components

### Navigation
- Clean top bar with logo left, utility links right
- Fixed position with subtle shadow on scroll
- Height: h-16, padding: px-8

### Main Interface
**Split Layout Design**:
- Left Panel (40%): Input/configuration area
  - Persona selector dropdown
  - Text input area (textarea with min-h-48)
  - Action buttons (Generate, Critique)
  - Settings accordion for advanced options
  
- Right Panel (60%): Output/results display
  - Generated content card with proper spacing
  - Critique feedback section with structured layout
  - Copy/export controls

### Form Elements
- Input fields: rounded-lg border with focus:ring treatment
- Textarea: rounded-lg with resize-y enabled
- Buttons: px-6 py-3 rounded-lg font-medium
  - Primary: filled style for main actions
  - Secondary: outline style for auxiliary actions
- Dropdowns: Custom styled select with chevron icon

### Content Cards
- Background: subtle background differentiation
- Border: rounded-xl
- Padding: p-8
- Shadow: subtle elevation (shadow-sm)

### Icons
**Library**: Heroicons via CDN
- Interface icons: 20px (w-5 h-5) for inline elements
- Feature icons: 24px (w-6 h-6) for standalone elements
- Use outline variant for navigation, solid for status indicators

## Page Structure

### Landing Page (index.html)
**Hero Section** (h-screen):
- Centered layout with max-w-4xl
- Large headline explaining AI content generation capability
- Subheading describing Ragie integration benefit
- Primary CTA button ("Get Started" → launches main interface)
- Secondary link ("Learn More" → scrolls to features)

**Features Section** (py-20):
- Three-column grid (grid-cols-1 md:grid-cols-3 gap-8)
- Feature cards with:
  - Icon at top
  - Feature title (text-xl font-semibold)
  - Description (text-base, 2-3 lines)
- Features: "AI Generation", "Smart Critique", "Custom Personas"

**How It Works** (py-20):
- Single column max-w-3xl
- Numbered steps with left border accent
- Each step: Icon + Title + Description
- Visual flow indicators between steps

**CTA Section** (py-16):
- Centered with max-w-2xl
- Bold statement about capabilities
- Large primary button
- Supporting text underneath

### Application Interface
**Single-page app layout**:
- Top navigation bar
- Main content area with split panel design
- Status indicators for API connections
- Toast notifications for actions (top-right positioning)

## Images
**Hero Image**: Yes - Abstract AI/technology themed illustration
- Placement: Background element behind hero text with overlay
- Style: Geometric, modern, tech-forward aesthetic
- Treatment: Subtle gradient overlay for text readability

**Feature Icons**: Use Heroicons (Sparkles, ChatBubbleLeftRight, UserGroup)

**Optional Illustrations**: Small spot illustrations for "How It Works" steps

## Component Specifications

### Input Area
- Label above input: text-sm font-medium mb-2
- Textarea: Full width, border-2, rounded-lg, p-4
- Character count: text-xs text-right mt-1
- Helper text: text-sm below input

### Output Display
- Code block styling for generated content
- Copy button: Absolute positioned top-right of content block
- Timestamp: text-xs at bottom
- Version history: Collapsible accordion

### Loading States
- Skeleton screens for content areas
- Spinner with descriptive text ("Generating content...")
- Progress indicators for multi-step processes

### Empty States
- Centered icon + message
- Suggested action button below
- Helpful tips or examples

## Responsive Behavior
- Desktop (lg+): Full split panel layout
- Tablet (md): Stacked panels with tabs to switch
- Mobile: Single column, progressive disclosure
- Breakpoints: sm:640px, md:768px, lg:1024px, xl:1280px

## Interaction Patterns
- Form validation: Inline error messages below fields
- Success feedback: Green checkmark icon + message
- Hover states: Subtle scale (scale-105) or opacity change
- Focus states: Ring treatment (focus:ring-2)

**Animations**: Minimal - only fade-in for content appearance and smooth scrolling