/** @odoo-module **/
const pathname = window.location.pathname;
if (/^\/(nasqo|shop)(\/|$)/.test(pathname)) {
    document.documentElement.setAttribute("dir", "rtl");
    document.documentElement.classList.add("nasqo-rtl-page");
}
