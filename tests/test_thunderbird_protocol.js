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
 console.log('Thunderbird JS handshake OK');
})().catch(e=>{console.error(e);process.exit(1)});
