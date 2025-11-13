
// Функція для генерації випадкового унікального ID (для чистих імен файлів)
function generateRandomId() {
  return Math.random().toString(36).substring(2, 9);
}

// 1. Створюємо ДВА пункти контекстного меню при встановленні
chrome.runtime.onInstalled.addListener(() => {
  // Пункт 1: Апскейл одного зображення
  chrome.contextMenus.create({
    id: "upscaleImage",
    title: "Upscale this image (Real-ESRGAN)",
    contexts: ["image"]
  });
  
  // Пункт 2: Апскейл ВСІЄЇ сторінки/глави
  chrome.contextMenus.create({
    id: "upscaleChapter",
    title: "Upscale Full Chapter (Real-ESRGAN)",
    contexts: ["page"] 
  });
});

// 2. Обробник кліків по контекстному меню
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "upscaleImage") {
    // --- ЛОГІКА ДЛЯ ОДНОГО ЗОБРАЖЕННЯ ---
    let url = new URL(info.srcUrl);
    // Використовуємо 'pathname' для отримання чистого шляху без параметрів запиту
    let originalFilename = url.pathname.split("/").pop(); 
    
    // Розділяємо ім'я та розширення
    let nameParts = originalFilename.split('.');
    let ext = nameParts.length > 1 ? '.' + nameParts.pop() : '';
    let baseName = nameParts.join('.');
    
    // Створюємо нове, унікальне ім'я файлу: [baseName]_[randomId].[ext]
    let newFilename = `${baseName}_${generateRandomId()}${ext}`;
    
    chrome.downloads.download({
      url: info.srcUrl,
      // Шлях відносний до папки Downloads (працює завдяки Symbolic Link)
      filename: "MangaUpscale/input/" + newFilename, 
      conflictAction: 'overwrite'
    });
    
  } else if (info.menuItemId === "upscaleChapter") {
    // --- ЛОГІКА ДЛЯ ВСІЄЇ ГЛАВИ ---
    
    // Запускаємо Content Script для отримання всіх URL-адрес зображень
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: getChapterImageUrls 
    }, (injectionResults) => {
      if (injectionResults && injectionResults[0] && injectionResults[0].result) {
        const urls = injectionResults[0].result;
        urls.forEach((url, index) => {
          
          // Генеруємо унікальне ім'я з індексом для сортування в черзі
          let originalFilename = new URL(url).pathname.split("/").pop();
          let ext = originalFilename.split('.').pop();
          let baseName = originalFilename.substring(0, originalFilename.lastIndexOf('.'));
          
          // Нове ім'я: chapter_page_01_baseName.ext
          let newFilename = `chapter_page_${String(index + 1).padStart(3, '0')}_${baseName}.${ext}`;

          chrome.downloads.download({
            url: url,
            filename: "MangaUpscale/input/" + newFilename,
            conflictAction: 'overwrite'
          });
        });
        alert(`Початок завантаження ${urls.length} зображень для апскейлу!`);
      } else {
        alert("Не вдалося знайти URL-адреси зображень. Спробуйте клікнути ПКМ на окремому зображенні.");
      }
    });
  }
});

// 3. Функція, яка виконується на сторінці манги (Content Script)
function getChapterImageUrls() {
  const imageUrls = new Set();
  
  document.querySelectorAll('img').forEach(img => {
    // зображення повинне бути досить широким (більше 500px)
    // або мати типовий для манги клас.
    if (img.naturalWidth > 500 || img.classList.contains('chapter-img') || img.classList.contains('page-image') || img.alt.includes('page')) {
      if (img.src && img.src.startsWith('http')) {
        imageUrls.add(img.src);
      }
    }
  });

  // Шукаємо зображення, які можуть бути фоном CSS (для вебтунів)
  document.querySelectorAll('div').forEach(div => {
    const style = window.getComputedStyle(div);
    const bgImage = style.backgroundImage;
    if (bgImage && bgImage !== 'none') {
        const match = bgImage.match(/url\(['"]?(.*?)['"]?\)/);
        if (match && match[1] && match[1].startsWith('http')) {
             imageUrls.add(match[1]);
        }
    }
  });

  // Повертаємо масив унікальних URL-адрес
  return Array.from(imageUrls);
}
