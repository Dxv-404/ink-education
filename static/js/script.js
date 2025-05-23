// File: static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const navMap = {
      bounty: "/bounties",
      marketplace: "/marketplace",
      tutoring: "/tutoring",
      qna: "/qna"
    };
  
    Object.keys(navMap).forEach(key => {
      document.querySelector(`.${key}`).addEventListener('click', () => {
        window.location.href = navMap[key];
      });
    });
  });
  