---
name: watermark-guide
description: Watermark configuration guide for article-illustrator-prompts
---

# Watermark Guide

## Position Diagram

```
┌─────────────────────────────┐
│                  [top-right]│
│                             │
│                             │
│      ILLUSTRATION           │
│                             │
│                             │
│[bottom-left][bottom-center][bottom-right]│
└─────────────────────────────┘
```

## Position Recommendations

| Position | Best For | Avoid When |
|----------|----------|------------|
| `bottom-right` | Default choice, most common | Key content in bottom-right |
| `bottom-left` | Right-heavy layouts | Key visual in bottom-left |
| `bottom-center` | Centered designs | Text-heavy bottom area |
| `top-right` | Bottom-heavy content | Header/logo in top-right |

## Content Format

| Format | Example | Style |
|--------|---------|-------|
| Handle | `@username` | Social media |
| Domain | `myblog.com` | Cross-platform |
| Brand | `MyBrand` | Simple branding |
| Chinese | `博客名` | Chinese platforms |

## Best Practices

1. **Consistency**: Use same watermark across all illustrations
2. **Legibility**: Ensure watermark readable on both light/dark areas
3. **Subtlety**: Keep subtle - should not distract from main illustration
4. **Placement**: Consider the illustration composition when choosing position

## Prompt Integration

When watermark is enabled, add to the prompt:

```
Include a subtle watermark "[content]" positioned at [position].
The watermark should be integrated naturally with the illustration style
and not distract from the main visual content.
```

## Style-Specific Considerations

| Style | Watermark Approach |
|-------|-------------------|
| notion | Simple text, bottom-right |
| warm | Hand-drawn style watermark |
| flat | Clean geometric watermark |
| watercolor | Organic, blended watermark |
| pixel | Pixelated watermark style |

## Common Issues

| Issue | Solution |
|-------|----------|
| Watermark invisible | Adjust position or check contrast |
| Watermark too prominent | Change position or reduce size |
| Watermark overlaps content | Change position based on illustration layout |
