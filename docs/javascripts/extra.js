document.addEventListener("DOMContentLoaded", function() {
  const hero = document.querySelector('.hero-container');
  if (hero) {
    // 1. 在这里按顺序填入你的图片路径
    const images = [
      'assets/homepage/bg1.jpg',   // 第一张图
      'assets/homepage/bg2.jpg',   // 第二张图
      'assets/homepage/bg3.png',   // 第三张图
      'assets/homepage/bg4.jpg',   // 第四张图
      // 如果你有更多图片，按这个格式往下加即可
    ];
    
    // 【新增：预加载所有图片】
    // 这样浏览器会在后台提前下载好这些图片，切换时就会绝对丝滑
    images.forEach(src => {
      const img = new Image();
      img.src = src;
    });

    let currentIndex = 0;
    // 初始化显示第一张图
    hero.style.backgroundImage = `url('${images[currentIndex]}')`;

    // 2. 设置定时器，每 5000 毫秒 (5秒) 切换一次图片
    setInterval(() => {
      currentIndex = (currentIndex + 1) % images.length;
      hero.style.backgroundImage = `url('${images[currentIndex]}')`;
    }, 5000); // 你可以修改 5000 来调整切换速度
  }
});