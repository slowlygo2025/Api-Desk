/**
 * Bitdefender / cupones / VPN inyectan atributos (bis_skin_checked, etc.)
 * en el DOM antes de que React hidrate. Este script corre en <head>
 * y los elimina en cuanto aparecen para que el HTML coincida con el SSR.
 */
(function () {
  var EXACT = {
    bis_skin_checked: true,
    bis_register: 1,
    "data-atm-ext-installed": true,
  };

  function shouldStrip(name) {
    return !!(name && (EXACT[name] || name.indexOf("__processed_") === 0));
  }

  function stripNode(el) {
    if (!el || !el.attributes || !el.removeAttribute) return;
    for (var i = el.attributes.length - 1; i >= 0; i--) {
      var n = el.attributes[i].name;
      if (shouldStrip(n)) el.removeAttribute(n);
    }
  }

  function stripTree(root) {
    if (!root) return;
    stripNode(root);
    if (!root.querySelectorAll) return;
    var nodes = root.querySelectorAll("*");
    for (var i = 0; i < nodes.length; i++) stripNode(nodes[i]);
  }

  function start() {
    var root = document.documentElement;
    if (!root) return;
    stripTree(root);
    new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var m = mutations[i];
        if (m.type === "attributes" && shouldStrip(m.attributeName)) {
          m.target.removeAttribute(m.attributeName);
        }
        var added = m.addedNodes;
        if (!added) continue;
        for (var j = 0; j < added.length; j++) {
          if (added[j].nodeType === 1) stripTree(added[j]);
        }
      }
    }).observe(root, { subtree: true, childList: true, attributes: true });
  }

  start();
})();
