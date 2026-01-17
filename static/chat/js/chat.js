let socket = null;
let recorder = null;
let audioChunks = [];
let typingTimeout = null;
let reconnectTimer = null;

function initChat(chatId, username, csrf) {

 if(!chatId) return;

 if(socket && socket.readyState === WebSocket.OPEN){
   socket.close();
 }

 const protocol = location.protocol === "https:" ? "wss" : "ws";
 const wsUrl = `${protocol}://${location.host}/ws/chat/${chatId}/`;

 socket = new WebSocket(wsUrl);

 const chatBox = document.getElementById("chat-box");
 const typingBox = document.getElementById("typing");
 const input = document.getElementById("messageInput");

 const scrollBottom = () => {
   if(chatBox) chatBox.scrollTop = chatBox.scrollHeight;
 };

 socket.onopen = () => {
   console.log("WS connected");
   scrollBottom();
 };

 socket.onclose = () => {
   console.log("WS reconnect...");
   if(!reconnectTimer){
     reconnectTimer = setTimeout(()=>{
       reconnectTimer = null;
       initChat(chatId, username, csrf);
     },1200);
   }
 };

 socket.onmessage = (e) => {

   let data;
   try {
     data = JSON.parse(e.data);
   } catch {
     return;
   }

   // unread badge update
   if(data.unread_count !== undefined){

     const badge = document.getElementById("unreadBadge");

     if(badge){
       if(data.unread_count > 0){
         badge.innerText = data.unread_count;
         badge.style.display = "inline-block";
       } else {
         badge.style.display = "none";
       }
     }

     return;
   }

   // typing
   if(data.typing){
     typingBox.innerText = data.username + " is typing...";
     return;
   }

   typingBox.innerText = "";

   const div = document.createElement("div");
   div.classList.add("message");

   if(data.username === username){
     div.classList.add("me");
     div.innerHTML = `<div class="sender">You</div>${data.message || ""}`;
   } else {
     div.classList.add("other");
     div.innerHTML = `<div class="sender">${data.username}</div>${data.message || ""}`;
   }

   chatBox.appendChild(div);
   scrollBottom();
 };

 // typing debounce
 if(input){
   input.oninput = () => {

     if(socket.readyState !== WebSocket.OPEN) return;

     socket.send(JSON.stringify({typing:true}));

     clearTimeout(typingTimeout);

     typingTimeout = setTimeout(()=>{
       typingBox.innerText="";
     },1200);
   };

   input.onkeydown = (e)=>{
     if(e.key==="Enter" && !e.shiftKey){
       e.preventDefault();
       sendMessage();
     }
   };
 }

 window.sendMessage = () => {

   if(!input) return;

   const text = input.value.trim();
   if(!text) return;

   if(socket.readyState !== WebSocket.OPEN) return;

   socket.send(JSON.stringify({message:text}));
   input.value="";
 };

 window.sendFile = () => {

   const fileInput=document.getElementById("fileInput");
   if(!fileInput?.files[0]) return;

   const form=new FormData();
   form.append("file",fileInput.files[0]);

   fetch(`/upload-file/${chatId}/`,{
     method:"POST",
     body:form,
     headers:{"X-CSRFToken":csrf}
   });

   fileInput.value="";
 };

 window.recordVoice = async ()=>{

   try{

     const stream = await navigator.mediaDevices.getUserMedia({audio:true});
     recorder = new MediaRecorder(stream);
     audioChunks=[];

     recorder.start();

     recorder.ondataavailable = e => audioChunks.push(e.data);

     recorder.onstop = ()=>{

       const blob = new Blob(audioChunks,{type:"audio/webm"});
       const form = new FormData();

       form.append("audio",blob);

       fetch(`/upload-voice/${chatId}/`,{
         method:"POST",
         body:form,
         headers:{"X-CSRFToken":csrf}
       });
     };

     setTimeout(()=>{
       if(recorder?.state==="recording") recorder.stop();
     },4000);

   } catch(err){
     console.warn("Mic error",err);
   }
 };

}

// ================= UI =================

window.toggleTheme = ()=>{
 document.body.classList.toggle("dark");
};

window.toggleProfile = ()=>{

 const drawer=document.getElementById("profileDrawer");
 const overlay=document.getElementById("profileOverlay");

 if(!drawer || !overlay) return;

 drawer.classList.toggle("active");
 overlay.classList.toggle("active");
};

window.closeProfile = ()=>{

 const drawer=document.getElementById("profileDrawer");
 const overlay=document.getElementById("profileOverlay");

 drawer.classList.remove("active");
 overlay.classList.remove("active");
};

document.addEventListener("keydown",e=>{
 if(e.key==="Escape") closeProfile();
});
