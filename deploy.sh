#!/bin/bash

# Build the project
echo "Building project..."
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "Build failed! dist directory not found."
    exit 1
fi

echo "Build successful!"

# Optional: Deploy using Wrangler (if installed)
if command -v wrangler &> /dev/null; then
    echo "Deploying to Cloudflare Pages..."
    wrangler pages deploy dist
else
    echo "Wrangler not found. Please install it to deploy automatically:"
    echo "npm install -g wrangler"
    echo ""
    echo "Or manually upload the 'dist' folder to Cloudflare Pages:"
    echo "https://dash.cloudflare.com"
fi
