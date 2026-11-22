/* Service worker for the exam-papers app.
   All URLs are relative to this file, so the app works from a GitHub Pages
   project path such as https://username.github.io/repository/ as well as
   from a domain root. Bump CACHE when the app shell changes. */
var CACHE = "exam-papers-v2";
var SHELL = [
  "./",
  "./index.html",
  "./data.js",
  "./manifest.webmanifest",
  "./favicon.svg",
  "./favicon.ico",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-192.png",
  "./icons/icon-maskable-512.png"
];

function scopeURL(path){
  return new URL(path, self.registration.scope).href;
}

self.addEventListener("install", function(event){
  event.waitUntil(
    caches.open(CACHE).then(function(cache){
      return cache.addAll(SHELL.map(scopeURL));
    }).then(function(){
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function(event){
  event.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(key){
        return key !== CACHE;
      }).map(function(key){
        return caches.delete(key);
      }));
    }).then(function(){
      return self.clients.claim();
    })
  );
});

/* Network first so a new deployment is picked up immediately; fall back to
   the cache (or the cached app shell for navigations) when offline. */
self.addEventListener("fetch", function(event){
  var request = event.request;
  if(request.method !== "GET") return;
  var url = new URL(request.url);
  if(url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(request).then(function(response){
      if(response && response.status === 200 && response.type === "basic"){
        var copy = response.clone();
        caches.open(CACHE).then(function(cache){
          cache.put(request, copy);
        });
      }
      return response;
    }).catch(function(){
      return caches.match(request).then(function(hit){
        if(hit) return hit;
        if(request.mode === "navigate") return caches.match(scopeURL("./index.html"));
        return Response.error();
      });
    })
  );
});
