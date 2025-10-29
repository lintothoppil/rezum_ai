# Education Section Validation Logic

## Field-Level Validation Rules

### Degree/Course Name
- Must be selected from the dropdown list or entered manually if "Other" is selected
- Cannot be empty
- Maximum length: 100 characters

### Institution Name
- Cannot be empty
- Maximum length: 150 characters
- Should not contain special characters except for standard punctuation

### Start Year
- Must be a 4-digit integer
- Must be between 1950 and current year + 5
- Cannot be greater than End Year (if End Year is specified)

### End Year
- Must be a 4-digit integer
- Must be between 1950 and 2030
- Cannot be less than Start Year
- **Validation Rule**: If End Year < 2026, show error: "End year cannot be earlier than 2026. Please correct your entry."

### Currently Studying
- Boolean value (true/false)
- If true, End Year field should be disabled/hidden

## Cross-Field Validation Rules

1. If "Currently Studying" is checked:
   - End Year field should be disabled
   - End Year value should not be required

2. If "Currently Studying" is unchecked:
   - End Year field should be enabled
   - End Year value should be required

3. Start Year must always be less than or equal to End Year (if End Year is provided)

4. For the latest qualification (first entry in the list):
   - If "Currently Studying" is false and End Year is in the future, it's valid
   - If "Currently Studying" is false and End Year is in the past, show warning but allow submission

## Error Messages

1. **Empty Fields**:
   - "Please enter your course name."
   - "Please enter your institution name."
   - "Please enter the start year."

2. **Invalid Year Format**:
   - "Please enter a valid 4-digit year."
   - "Year must be between 1950 and 2030."

3. **Year Comparison Errors**:
   - "Start year cannot be later than end year."
   - "End year cannot be earlier than 2026. Please correct your entry."

4. **Currently Studying Conflicts**:
   - "Please uncheck 'Currently Studying' to enter an end year."
   - "Please enter an end year or check 'Currently Studying'."

## Real-Time Validation Triggers

1. On field blur (when user moves away from a field)
2. On form submission attempt
3. On dependent field changes (e.g., when "Currently Studying" is toggled)

## Validation Implementation Notes

1. Client-side validation should provide immediate feedback
2. Server-side validation should always be performed for security
3. All validation errors should be displayed inline next to the relevant fields
4. Form should not be submitted if any validation errors exist
5. Validations should be performed in the following order:
   a. Required field checks
   b. Format validation
   c. Cross-field validation
   d. Business rule validation