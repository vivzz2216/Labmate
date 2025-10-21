# Testing React SPA Multi-File Support

## Test Document Example

Create a Word document (.docx) with the following content:

---

# Experiment 6 – Single Page Application using React Router

## Aim
Design a Single Page Application (SPA) using React Router.

## Folder Structure
```
react-spa/
 ├── src/
 │   ├── components/
 │   │   ├── Home.js
 │   │   ├── About.js
 │   │   ├── Contact.js
 │   │   └── Navbar.js
 │   ├── App.js
 │   ├── index.js
 │   └── App.css
 ├── package.json
 └── ...
```

## Code Files

### src/App.js
```javascript
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import About from "./components/About";
import Contact from "./components/Contact";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <div className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
```

### src/components/Navbar.js
```javascript
import React from "react";
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">
      <h2>My React SPA</h2>
      <ul>
        <li><Link to="/">Home</Link></li>
        <li><Link to="/about">About</Link></li>
        <li><Link to="/contact">Contact</Link></li>
      </ul>
    </nav>
  );
}

export default Navbar;
```

### src/components/Home.js
```javascript
import React from "react";

function Home() {
  return (
    <div className="page">
      <h1>Welcome to the Home Page</h1>
      <p>This is a Single Page Application built using React Router.</p>
    </div>
  );
}

export default Home;
```

### src/components/About.js
```javascript
import React from "react";

function About() {
  return (
    <div className="page">
      <h1>About Us</h1>
      <p>We are learning how to create dynamic and responsive SPAs using React.</p>
    </div>
  );
}

export default About;
```

### src/components/Contact.js
```javascript
import React from "react";

function Contact() {
  return (
    <div className="page">
      <h1>Contact Us</h1>
      <p>Email: contact@example.com</p>
      <p>Phone: +91 99999 99999</p>
    </div>
  );
}

export default Contact;
```

### src/App.css
```css
body {
  font-family: 'Segoe UI', sans-serif;
  background-color: #f8f9fa;
  margin: 0;
  padding: 0;
}

.navbar {
  background-color: #333;
  color: white;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar ul {
  list-style-type: none;
  display: flex;
  gap: 20px;
}

.navbar ul li a {
  color: white;
  text-decoration: none;
}

.navbar ul li a:hover {
  color: #61dafb;
}

.page {
  padding: 40px;
  text-align: center;
}

.page h1 {
  color: #333;
}
```

## Commands to Run
```bash
# Create app
npx create-react-app react-spa
cd react-spa

# Install react-router-dom
npm install react-router-dom

# Run app
npm start
```

## Expected Output
A single page app with navigation links for Home, About, and Contact.
The page content changes without reloading, demonstrating SPA behavior.

---

## Testing Steps

1. **Navigate to**: http://localhost:3000 (or your deployed URL)

2. **Log in** with your credentials

3. **Upload the test document**:
   - Click "Upload Assignment"
   - Select the .docx file
   - Choose language: **React** (if prompted)

4. **AI Analysis**:
   - AI should detect this as a "React SPA Project"
   - Should show:
     - Task type: "React SPA Project" (with cyan icon)
     - Project Files: 6 files listed
       - src/App.js
       - src/components/Navbar.js
       - src/components/Home.js
       - src/components/About.js
       - src/components/Contact.js
       - src/App.css
     - Routes: `/`, `/about`, `/contact` (as cyan badges)
     - Expandable "View all file contents" section

5. **Select the task** and click "Submit Selected Tasks"

6. **Execution** (this takes 90-120 seconds):
   - Backend creates temp project directory
   - Spawns Node.js Docker container
   - Runs `npm install` (installs React, react-router-dom, Vite)
   - Starts Vite dev server
   - Captures screenshots of all 3 routes

7. **Expected Results**:
   - Status: "Completed"
   - 3 screenshots generated:
     - Route: `/` (Home page)
     - Route: `/about` (About page)
     - Route: `/contact` (Contact page)
   - Each screenshot shows VS Code UI with code and browser preview
   - Caption: "React SPA project with 3 routes captured successfully"

## Troubleshooting

### If execution fails:
- Check Docker containers: `docker ps`
- View backend logs: `docker compose logs backend --follow`
- Check if port 3001 is available
- Verify npm packages installed correctly

### If AI doesn't detect as React project:
- Ensure at least 2 of these patterns are present:
  - `react-router` or `BrowserRouter`
  - Component files (Navbar, Home, etc.)
  - `package.json` or `npm install`
  - `App.js` or `function App`

### If screenshots don't capture routes:
- Check if routes are extracted correctly
- Verify Vite dev server started successfully
- Check Playwright logs in backend output

## Success Indicators
✅ Task type shows "React SPA Project"
✅ 6 files listed in project view
✅ 3 routes shown as badges
✅ Execution completes in ~120 seconds
✅ 3 screenshots generated
✅ Each screenshot shows different page content
✅ VS Code UI visible with browser preview

