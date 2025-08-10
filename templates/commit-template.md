# Commit Message Template

## Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **perf**: Performance improvements
- **ci**: CI/CD changes
- **security**: Security-related changes

## Scopes
- **ai**: AI/ML model changes
- **extension**: Chrome extension changes
- **api**: API changes
- **ui**: User interface changes
- **backend**: Backend service changes
- **frontend**: Frontend application changes
- **test**: Test-related changes
- **docs**: Documentation changes

## Examples

### Feature Implementation
```
feat(ai): implement bias detection algorithm

- Add sentiment analysis for content bias detection
- Integrate with OpenAI API for text analysis
- Add unit tests for bias detection accuracy
- Update documentation with bias detection guidelines

Closes #123
```

### Bug Fix
```
fix(extension): resolve YouTube page layout detection issue

- Fix selector for YouTube's new layout
- Add fallback detection methods
- Update tests for layout changes
- Improve error handling for layout detection

Fixes #456
```

### Performance Improvement
```
perf(api): optimize YouTube API response processing

- Implement caching for API responses
- Reduce API call frequency
- Add rate limiting protection
- Update performance benchmarks

Improves response time by 40%
```

### Security Update
```
security(backend): implement API key encryption

- Encrypt API keys in database
- Add key rotation mechanism
- Update security documentation
- Add security audit logging

Addresses security vulnerability #789
```

### Documentation Update
```
docs(feature): update AI model documentation

- Add detailed explanation of credibility scoring
- Document bias detection methodology
- Update API documentation
- Add troubleshooting guide

Improves developer onboarding
```

## Guidelines

### Subject Line
- Use imperative mood ("add" not "added")
- Keep under 50 characters
- Start with lowercase letter
- No period at the end

### Body
- Explain what and why, not how
- Wrap at 72 characters
- Use bullet points for multiple changes

### Footer
- Reference related issues
- Include breaking change notes
- Add co-authors if applicable

## Breaking Changes
For breaking changes, add `BREAKING CHANGE:` to the footer:

```
feat(api): change credibility scoring algorithm

BREAKING CHANGE: Credibility scores now range from 0-100 instead of 0-10
```

## Info-Guard Specific Notes
- Always mention AI/ML impact when relevant
- Include privacy considerations in security commits
- Reference bias detection accuracy in AI-related commits
- Note Chrome extension compatibility in UI commits 