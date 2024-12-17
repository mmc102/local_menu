/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./templates/**/*.html", 
        "./static/**/*.js",     
    ],
    theme: {
        extend: {},
    },
    safelist: [
        "bg-blue-500",
        "bg-blue-800",
        "bg-blue-700",
    ],
    plugins: [],
};
