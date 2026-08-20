# AWS DevOps Agent Demo - Frontend

React + TypeScript + Vite frontend for the AWS DevOps Agent demonstration portal. It is served as static assets from Amazon S3 behind Amazon CloudFront and is built and deployed by the CDK frontend stack.

## Features

- **Process Order**: Button that calls the backend to process an order (which fails by design, triggering the incident).
- **Incident Banner**: Shows incident status and a running resolution timer.
- **Architecture and Business Diagrams**: Toggle between a business view and a technical AWS architecture view.
- **Reset Demo**: Button that returns the portal to a clean state for the next run.
- **Responsive Design**: Clean, modern UI built with Tailwind CSS.

## Build

```bash
# Install dependencies
npm install
```

```bash
# Build for production
npm run build
```

Verify the build succeeded — the build writes static assets to `dist/`:

```bash
ls dist/   # expect index.html and an assets/ directory
```

The production build is deployed by the CDK frontend stack (`cdk deploy "dev/frontend"`), which uploads the assets to Amazon S3 and injects runtime configuration via `/runtime-config.js`. There is no local dev server; the app reads its Amazon Cognito and Amazon API Gateway settings from the runtime config deployed to Amazon S3.

## Requirements

- Node.js 22+

## Architecture

The frontend is built with:
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first styling

At runtime the app calls the Amazon API Gateway endpoint defined in `/runtime-config.js`, which the CDK frontend stack deploys to Amazon S3 after the API and authentication resources are created.

## Conclusion

This frontend provides a clean, responsive interface for demonstrating AWS DevOps Agent incident detection and diagnosis. It connects to the backend through Amazon API Gateway and displays real-time incident status and resolution timing. For deployment instructions, see the main project [README](../../README.md) and [QUICKSTART.md](../../QUICKSTART.md).
