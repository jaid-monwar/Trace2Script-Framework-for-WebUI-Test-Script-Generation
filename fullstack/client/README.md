# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/42639286-316b-4606-bbd6-a84faf643b05

## API Key Encryption Setup

This project includes API key encryption functionality using RSA public/private key pairs. To set up encryption, you'll need to generate a key pair and configure the public key in your environment.

### Generate RSA Key Pair

Use OpenSSL to generate the required keys:

```bash
# Generate private key (2048-bit RSA)
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048

# Extract public key from private key
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

### Configure Environment

1. Copy the contents of `public_key.pem`
2. Convert the multi-line public key to a single line format with escaped newlines
3. Update the `VITE_PUBLIC_KEY` variable in your `.env` file with the formatted key
4. Keep the `private_key.pem` secure on your backend server for decryption

**Example .env configuration:**
```bash
VITE_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqh...your_key_here...\n-----END PUBLIC KEY-----"
```

**Converting multi-line to single line:**
- Replace all actual newlines with `\n`
- Keep the key as one continuous string
- Ensure proper escaping of the newline characters

### Security Notes

- **Never commit private keys** to version control
- Store the private key securely on your backend server
- The public key in `.env` is safe to include in your frontend build
- API keys entered in the application will be automatically encrypted before transmission

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/42639286-316b-4606-bbd6-a84faf643b05) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/42639286-316b-4606-bbd6-a84faf643b05) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
