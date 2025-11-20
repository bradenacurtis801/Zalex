# Documentation

This directory contains comprehensive documentation for the AI Document Agent system.

## Documentation Index

### Core Components

- **[Classifier Documentation](classifier.md)** - Document classification system using similarity-based methods
- **[API Documentation](../backend/README.md)** - Backend API endpoints and services
- **[Frontend Documentation](../frontend/README.md)** - Frontend components and user interface
- **[Training Documentation](../train/README.md)** - Model training and data processing

### System Architecture

- **[Main README](../README.md)** - Overall system overview and getting started guide
- **[Docker Documentation](../DOCKER.md)** - Container deployment and configuration

## Quick Start

1. **Understanding the System**: Start with the [Main README](../README.md)
2. **Training Models**: See [Training Documentation](../train/README.md)
3. **Running the System**: Follow [Docker Documentation](../DOCKER.md)
4. **API Integration**: Reference [API Documentation](../backend/README.md)

## Document Classification

The core of is its document classification system. Key concepts:

- **Similarity-based Classification**: Uses SentenceTransformer embeddings and cosine similarity
- **768-dimensional Vectors**: Each document is converted to a 768-number vector
- **Category Embeddings**: Pre-computed average vectors for each document type
- **Real-time Processing**: Classifies documents as they're uploaded

For detailed information, see [Classifier Documentation](classifier.md).

## Contributing

When adding new features or making changes:

1. Update relevant documentation files
2. Add examples and usage patterns
3. Include troubleshooting information
4. Update this index if adding new documentation files

## Support

For questions or issues:

1. Check the relevant documentation first
2. Review troubleshooting sections
3. Check the main project README for setup issues
4. Open an issue on the project repository
