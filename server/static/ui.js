// App.js - Handles landing page to canvas transitions and UI enhancements

document.addEventListener('DOMContentLoaded', () => {
  const landingPage = document.getElementById('landing-page');
  const canvasApp = document.getElementById('canvas-app');
  const startButton = document.getElementById('start-button');
  const backButton = document.getElementById('back-button');
  const sizeSlider = document.getElementById('size-slider');
  const sizeValue = document.getElementById('size-value');
  const modeButtons = document.querySelectorAll('[data-mode]');

  // Landing page to canvas transition
  if (startButton) {
    startButton.addEventListener('click', () => {
      landingPage.style.opacity = '0';
      landingPage.style.transform = 'scale(0.95)';
      landingPage.style.transition = 'all 0.5s ease';
      
      setTimeout(() => {
        landingPage.style.display = 'none';
        canvasApp.style.display = 'flex';
        canvasApp.style.opacity = '0';
        
        requestAnimationFrame(() => {
          canvasApp.style.transition = 'opacity 0.5s ease';
          canvasApp.style.opacity = '1';
        });
      }, 500);
    });
  }

  // Back to landing page
  if (backButton) {
    backButton.addEventListener('click', () => {
      canvasApp.style.opacity = '0';
      canvasApp.style.transition = 'opacity 0.5s ease';
      
      setTimeout(() => {
        canvasApp.style.display = 'none';
        landingPage.style.display = 'flex';
        landingPage.style.opacity = '0';
        landingPage.style.transform = 'scale(0.95)';
        
        requestAnimationFrame(() => {
          landingPage.style.transition = 'all 0.5s ease';
          landingPage.style.opacity = '1';
          landingPage.style.transform = 'scale(1)';
        });
      }, 500);
    });
  }

  // Size slider value display
  if (sizeSlider && sizeValue) {
    sizeSlider.addEventListener('input', (e) => {
      sizeValue.textContent = e.target.value;
    });
  }

  // Mode button toggle (visual feedback)
  modeButtons.forEach(button => {
    button.addEventListener('click', () => {
      modeButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
    });
  });

  // Style the color palette buttons created by sand.js
  const palette = document.getElementById('palette');
  if (palette) {
    setTimeout(() => {
      const colorButtons = palette.querySelectorAll('button');
      
      colorButtons.forEach((colorBtn, index) => {
        const color = colorBtn.style.background;
        
        colorBtn.className = 'color-btn';
        colorBtn.style.cssText = `
          width: 28px;
          height: 28px;
          background: ${color};
          border: 3px solid rgba(255, 255, 255, 0.3);
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 2px 0 rgba(0, 0, 0, 0.3);
          image-rendering: pixelated;
        `;
        
        // Add hover effects
        colorBtn.addEventListener('mouseenter', function() {
          this.style.transform = 'scale(1.15)';
          this.style.borderColor = 'white';
          this.style.boxShadow = `0 4px 0 rgba(0, 0, 0, 0.3), 0 0 15px ${color}`;
        });
        
        colorBtn.addEventListener('mouseleave', function() {
          if (!this.classList.contains('active')) {
            this.style.transform = 'scale(1)';
            this.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            this.style.boxShadow = '0 2px 0 rgba(0, 0, 0, 0.3)';
          }
        });
        
        // Enhance the existing onclick to also update active state
        const originalOnClick = colorBtn.onclick;
        colorBtn.onclick = function(e) {
          // Call original sand.js click handler
          if (originalOnClick) originalOnClick.call(this, e);
          
          // Update visual active state
          palette.querySelectorAll('.color-btn').forEach(btn => {
            btn.classList.remove('active');
            btn.style.transform = 'scale(1)';
            btn.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            btn.style.boxShadow = '0 2px 0 rgba(0, 0, 0, 0.3)';
          });
          this.classList.add('active');
          this.style.transform = 'scale(1.15)';
          this.style.borderColor = 'white';
          this.style.boxShadow = `0 4px 0 rgba(0, 0, 0, 0.3), 0 0 15px ${color}`;
        };
        
        // Set first color as active by default
        if (index === 0) {
          colorBtn.classList.add('active');
          colorBtn.style.borderColor = 'white';
          colorBtn.style.transform = 'scale(1.15)';
          colorBtn.style.boxShadow = `0 4px 0 rgba(0, 0, 0, 0.3), 0 0 15px ${color}`;
        }
      });
    }, 100);
  }

  // Add particle animation to sand particles background
  const particlesContainer = document.querySelector('.sand-particles');
  if (particlesContainer) {
    // Create floating pixel particles
    for (let i = 0; i < 1000; i++) {
      const particle = document.createElement('div');
      particle.className = 'floating-particle';
      particle.style.cssText = `
        position: absolute;
        width: ${Math.random() * 4 + 2}px;
        height: ${Math.random() * 4 + 2}px;
        background: ${['#f4e4c1', '#dbc280', '#ff6b6b', '#4ecdc4', '#ffa07a'][Math.floor(Math.random() * 5)]};
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        opacity: ${Math.random() * 0.5 + 0.3};
        animation: float ${Math.random() * 10 + 10}s linear infinite;
        animation-delay: ${Math.random() * 5}s;
        image-rendering: pixelated;
      `;
      particlesContainer.appendChild(particle);
    }
  }

  // Add CSS for floating particles
  const style = document.createElement('style');
  style.textContent = `
    @keyframes float {
      0% {
        transform: translate(0, 0) rotate(0deg);
      }
      25% {
        transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) rotate(90deg);
      }
      50% {
        transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) rotate(180deg);
      }
      75% {
        transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) rotate(270deg);
      }
      100% {
        transform: translate(0, 0) rotate(360deg);
      }
    }
  `;
  document.head.appendChild(style);


});