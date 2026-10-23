/* Högerklick på mail i Thunderbird → spara avsändare i E-postofferten */

const NATIVE_HOST = "e_postofferten";
const PROTOCOL_VERSION = 1;

async function sendContacts(payload) {
  // Check before writing: old hosts may otherwise accept the import silently.
  const hello = await browser.runtime.sendNativeMessage(NATIVE_HOST, {
    action: "ping", protocol_version: PROTOCOL_VERSION,
  });
  if (!hello || !hello.ok || hello.protocol_version !== PROTOCOL_VERSION) {
    throw new Error("App och Thunderbird-tillägg är inte kompatibla. Uppdatera appen, installera dess MailOffer.xpi och registrera kopplingen igen.");
  }
  const result = await browser.runtime.sendNativeMessage(NATIVE_HOST, {
    ...payload, protocol_version: PROTOCOL_VERSION,
  });
  if (!result || result.protocol_version !== PROTOCOL_VERSION) {
    throw new Error("Inkompatibelt svar från appen. Installera senaste appen och XPI-filen.");
  }
  return result;
}

function parseAuthor(author) {
  const text = String(author || "").trim();
  if (!text) return null;
  const angle = text.match(/^(.*)<([^>]+@[^>]+)>\s*$/);
  if (angle) {
    return {
      name: angle[1].replace(/^["']|["']$/g, "").trim(),
      email: angle[2].trim().toLowerCase(),
    };
  }
  const mail = text.match(/([^<\s@]+@[^>\s@]+\.[^>\s@]+)/);
  if (!mail) return null;
  return { name: "", email: mail[1].trim().toLowerCase() };
}

async function selectedMessages(info, tab) {
  if (info && info.selectedMessages && info.selectedMessages.messages) {
    return info.selectedMessages.messages;
  }
  try {
    if (tab && tab.id != null) {
      const shown = await browser.messageDisplay.getDisplayedMessage(tab.id);
      if (shown) return [shown];
    }
  } catch (e) {}
  try {
    const listed = await browser.mailTabs.getSelectedMessages();
    if (listed && listed.messages) return listed.messages;
  } catch (e) {}
  return [];
}

async function saveAuthors(messages) {
  const contacts = [];
  const seen = new Set();
  for (const msg of messages) {
    const parsed = parseAuthor(msg.author || msg.from || "");
    if (!parsed || seen.has(parsed.email)) continue;
    seen.add(parsed.email);
    contacts.push(parsed);
  }
  if (!contacts.length) {
    throw new Error("Ingen avsändare hittades i det markerade mailet.");
  }
  const result = await sendContacts({
    action: "add_contacts",
    contacts: contacts,
  });
  if (!result || result.ok === false) {
    throw new Error(
      (result && result.error) ||
        "Kunde inte skriva till E-postofferten. Starta appen en gång så registreras kopplingen."
    );
  }
  return { contacts, result };
}

function notify(title, message) {
  if (browser.notifications) {
    browser.notifications.create({
      type: "basic",
      title: title,
      message: message,
    });
  }
}

browser.menus.create({
  id: "epostofferten-save-sender",
  title: "Spara avsändare i E-postofferten",
  contexts: ["message_list"],
});

try {
  browser.menus.create({
    id: "epostofferten-save-sender-display",
    title: "Spara avsändare i E-postofferten",
    contexts: ["page", "message_display"],
  });
} catch (e) {}

browser.menus.onClicked.addListener(async (info, tab) => {
  if (
    info.menuItemId !== "epostofferten-save-sender" &&
    info.menuItemId !== "epostofferten-save-sender-display"
  ) {
    return;
  }
  try {
    const messages = await selectedMessages(info, tab);
    const out = await saveAuthors(messages);
    const n = out.result.added + out.result.updated;
    notify(
      "E-postofferten",
      n
        ? "Sparade " + n + " kontakt(er) i appen."
        : "Kontakt(er) fanns redan i appen."
    );
  } catch (err) {
    notify("E-postofferten", String(err.message || err));
  }
});

// A clicked address takes precedence over the author of the displayed mail.
browser.menus.create({
  id: "mailoffer-address",
  title: "Skicka e-postadressen till E-postofferten",
  contexts: ["link"],
  targetUrlPatterns: ["mailto:*"],
});
browser.menus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "mailoffer-address") return;
  try {
    const address = decodeURIComponent(String(info.linkUrl || "").replace(/^mailto:/i, "").split("?")[0]);
    const contacts = address.split(/[,;]/).map(email => parseAuthor(email)).filter(Boolean);
    if (!contacts.length) throw new Error("Ingen giltig e-postadress hittades.");
    const result = await sendContacts({action: "add_contacts", contacts});
    if (!result || !result.ok) throw new Error((result && result.error) || "Starta appen en gång för att registrera kopplingen.");
    notify("E-postofferten", "Adressen har skickats till appens kontaktlista.");
  } catch (err) {
    notify("E-postofferten", String(err.message || err));
  }
});
