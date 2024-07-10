# ParchMark UI Regression Test Suite

## Core Functionality Tests

### Navigation and UI Elements

1. **Sidebar Visibility**
   - Verify sidebar displays by default
   - Toggle sidebar using the hamburger icon to hide/show
   - Confirm sidebar persists across page refreshes

2. **Note List**
   - Verify all notes appear in the sidebar
   - Confirm notes are sorted correctly
   - Check note titles display correctly with truncation for long titles
   - Verify note selection changes active note highlight

3. **Header Elements**
   - Verify ParchMark logo/text displays correctly
   - Confirm hamburger menu is visible and functional

### Note Management

4. **Create New Note**
   - Click "+" button to create a new note
   - Verify new note appears in sidebar
   - Confirm new note is automatically selected
   - Verify editor opens automatically in edit mode with template content
   - Verify cursor is positioned in the editor ready for typing

5. **Delete Note**
   - Select a note and click the trash icon
   - Verify note is removed from sidebar
   - Confirm another note is automatically selected
   - Test deletion of last note

6. **Note Selection**
   - Click on different notes in sidebar
   - Verify correct note content loads in the main area
   - Check for smooth transition between notes

### Note Editing

7. **Edit Mode**
   - Open a note and click "Edit" button
   - Verify transition to edit mode
   - Confirm title becomes editable
   - Confirm content area becomes a textarea

8. **Save Changes**
   - Make changes to note title and content
   - Click "Save" button
   - Verify changes persist
   - Confirm transition back to view mode
   - Verify title field and content area stay in sync (title reflects H1 heading)

9. **Markdown Rendering**
   - Create note with various markdown elements:
     - Headers (H1-H6)
     - Bold/italic text
     - Lists (ordered and unordered)
     - Links
     - Code blocks
     - Blockquotes
   - Verify proper rendering in view mode
   - Confirm H1 headings don't appear duplicated in content

## Visual and Responsive Tests

10. **Theme and Styling**
    - Verify consistent color scheme throughout app
    - Check font styles for headings and body text
    - Confirm hover states on buttons and interactive elements
    - Verify transitions and animations work smoothly

11. **Responsive Layout**
    - Test on multiple screen sizes:
      - Desktop (1920x1080)
      - Laptop (1366x768)
      - Tablet (768x1024)
      - Mobile (375x667)
    - Verify sidebar collapses appropriately on smaller screens
    - Confirm content remains readable across devices

## Edge Cases

12. **Empty State Handling**
    - Delete all notes and verify appropriate empty state message
    - Confirm "Create New Note" button works from empty state

13. **Content Overflow**
    - Test extremely long note titles
    - Test very large notes with extensive content
    - Verify scrolling works properly for large content

14. **Special Characters**
    - Test notes with emojis, special characters, and non-Latin scripts
    - Verify correct display in both edit and view modes

15. **Input Validation**
    - Test empty title submission
    - Verify app handles attempted submission of empty notes
    - Test notes with only an H1 heading and no additional content

## Performance Tests

16. **Load Time**
    - Measure initial page load time
    - Test load time with many notes (50+)
    - Verify code splitting works correctly with lazy-loaded components
    - Confirm component loading fallbacks display appropriately during chunk loading

17. **Interaction Responsiveness**
    - Measure time to switch between notes
    - Test responsiveness of edit/save operations
    - Verify smoothness of markdown preview rendering
    - Measure time to create new note and enter edit mode automatically

## Accessibility Tests

18. **Keyboard Navigation**
    - Verify all functionality accessible via keyboard
    - Test tab order is logical and complete

19. **Screen Reader Compatibility**
    - Test with screen reader software
    - Verify all elements have appropriate ARIA labels

20. **Color Contrast**
    - Verify text meets WCAG AA contrast requirements
    - Test readability of all UI elements

## Browser Compatibility

21. **Cross-browser Testing**
    - Test on Chrome, Firefox, Safari, and Edge
    - Verify consistent behavior across browsers

## Regression Tests for Specific Features

22. **Markdown Extensions**
    - Test GFM (GitHub Flavored Markdown) features:
      - Tables
      - Task lists
      - Strikethrough
      - Auto-linking

23. **Notes Navigation**
    - Test navigating between notes with keyboard shortcuts
    - Verify navigation history works correctly

24. **H1 Title Extraction**
    - Create a new note with an H1 heading (e.g., "# Test Heading")
    - Verify the H1 content is automatically used as the note title
    - Edit a note to change its H1 heading
    - Verify the note title updates accordingly upon save
    - Test with H1 headings containing special characters and formatting

25. **Template Text Removal**
    - Create a new note and observe the template text
    - Edit the note, keeping the template text "Start writing here..."
    - Save the note and verify the template text is removed
    - Check that the note appears clean in view mode
    
26. **Title Consistency**
    - Create notes with and without H1 headings
    - Verify titles in the sidebar match the appropriate H1 heading or user-entered title
    - Check that switching between notes maintains the correct title in both sidebar and note view
    
27. **Code Splitting**
    - Verify component chunks load correctly when navigating to a new route
    - Test fallback components appear during lazy loading
    - Confirm that components render correctly after loading completes
    - Test application behavior with slow network connection
    - Verify that edit mode starts automatically when creating a new note