# Contributing to Aethel

Thank you for your interest in contributing to Aethel! This document provides guidelines for contributing to the project.

## 🎯 Areas Where You Can Contribute

### 1. Core Language Development
- **Grammar Expansion**: Add support for loops, recursion, complex types
- **Judge Improvements**: Temporal logic, deadlock detection, performance optimization
- **Parser Enhancements**: Better error messages, syntax sugar

### 2. Vault & Distribution
- **P2P Synchronization**: Implement distributed vault synchronization
- **Bundle Optimization**: Improve bundle compression and verification
- **Certificate Management**: Enhanced cryptographic proofs

### 3. Runtime & Execution
- **WASM Optimization**: Improve WebAssembly compilation and execution
- **Weaver Enhancements**: Better hardware detection and adaptation
- **State Management**: Optimize Merkle tree operations

### 4. AI & Architect
- **Prompt Engineering**: Improve AI code generation quality
- **Learning Algorithms**: Enhance pattern learning from successful verifications
- **Constraint Suggestion**: Better guard/verify generation

### 5. Documentation & Examples
- **Tutorials**: Step-by-step guides for common use cases
- **Examples**: Real-world applications (DeFi, IoT, aerospace)
- **API Documentation**: Comprehensive API reference

### 6. Testing & Validation
- **Test Cases**: Add more comprehensive test coverage
- **Benchmarks**: Performance benchmarking suite
- **Fuzzing**: Automated testing for edge cases

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic understanding of formal verification (helpful but not required)

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/aethel-core
cd aethel-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest
```

## 📝 Contribution Process

### 1. Find or Create an Issue
- Check existing issues for something you'd like to work on
- Create a new issue if you have a new idea
- Comment on the issue to let others know you're working on it

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 3. Make Your Changes
- Write clean, readable code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```bash
# Run all tests
python -m pytest

# Run specific test
python test_your_module.py

# Run linting
flake8 aethel/
```

### 5. Commit Your Changes
```bash
git add .
git commit -m "feat: add new feature description"
# or
git commit -m "fix: fix bug description"
```

**Commit Message Format**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `perf:` Performance improvements

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Reference to related issues
- Screenshots/examples if applicable

## 🎨 Code Style Guidelines

### Python Code
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions focused and small

### Aethel Code
- Use clear, descriptive intent names
- Document complex guard/verify conditions
- Provide examples in comments

### Documentation
- Use Markdown for all documentation
- Include code examples
- Keep language clear and concise

## 🧪 Testing Guidelines

### Writing Tests
- Write tests for all new functionality
- Ensure tests are deterministic
- Use descriptive test names
- Include edge cases

### Test Structure
```python
def test_feature_name():
    """Test description"""
    # Arrange
    setup_code()
    
    # Act
    result = function_to_test()
    
    # Assert
    assert result == expected_value
```

## 📚 Documentation Guidelines

### Code Documentation
- All public APIs must have docstrings
- Include parameter types and return types
- Provide usage examples

### User Documentation
- Write for beginners and experts
- Include practical examples
- Link to related documentation

## 🐛 Reporting Bugs

When reporting bugs, please include:
- Aethel version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

## 💡 Suggesting Features

When suggesting features, please include:
- Clear description of the feature
- Use cases and benefits
- Potential implementation approach
- Examples of similar features in other systems

## 🤝 Code of Conduct

### Our Standards
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

### Unacceptable Behavior
- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Publishing private information

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check existing docs first

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## 📄 License

By contributing to Aethel, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for helping make Aethel better!**

The future is not written in code. It is proved in theorems.
