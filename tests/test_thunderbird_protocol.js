const vm = require('vm');
const fs = require('fs');
const assert = require('assert');
let calls = [];
let reply = {ok:true};
const browser = {menus:{create(){},onClicked:{addListener(){}}},runtime:{async sendNativeMessage(host,payload){calls.push(payload);return reply;}}};
const context = vm.createContext({browser, console});
vm.runInContext(fs.readFileSync('thunderbird/background.js','utf8'),context);
(async()=>{
 await assert.rejects(vm.runInContext('sendContacts({action:"add_contacts",contacts:[]})',context), /kompatibla/);
 assert.equal(calls.length,1);
 assert.equal(calls[0].action,'ping');
 calls=[];reply={ok:true,protocol_version:1};
 await vm.runInContext('sendContacts({action:"add_contacts",contacts:[]})',context);
 assert.equal(calls.length,2);
 assert.equal(calls[1].protocol_version,1);
 calls=[];
 reply={ok:true,protocol_version:1,capabilities:["import_images"],count:1};
 context.btoa = text => Buffer.from(text, 'binary').toString('base64');
 browser.messages={
   async listAttachments(){return [{contentType:"image/png",name:"photo.png",partName:"1.2"},{contentType:"application/pdf",name:"doc.pdf",partName:"1.3"}];},
   async getAttachmentFile(id,part){assert.equal(id,7);assert.equal(part,"1.2");return {name:"photo.png",size:8,async arrayBuffer(){return Uint8Array.from([137,80,78,71,13,10,26,10]).buffer;}};},
 };
 await vm.runInContext('importImages([{id:7,subject:"Example"}])',context);
 const payload = calls.find(x=>x.action==='import_images');
 assert(payload);
 assert.equal(payload.images.length,1);
 assert.equal(payload.images[0].data,'iVBORw0KGgo=');
 assert.equal(payload.subject,'Example');
 await assert.rejects(vm.runInContext('importImages([])',context), /ett mejl/);
 reply={ok:true,protocol_version:1};
 await assert.rejects(vm.runInContext('importImages([{id:7}])',context), /Uppdatera MailOffer/);
 console.log('Thunderbird JS handshake and image import OK');
})().catch(e=>{console.error(e);process.exit(1)});
