/** @odoo-module **/

/**
 * Set an intersection observer on the given element. This function will ensure
 * that the given callback function will be called at most once when the given
 * element becomes visible on screen. This function can be used to load
 * components lazily (see: 'EmbeddedViewBehavior').
 * @param {HTMLElement} element
 * @param {Function} callback
 * @returns {IntersectionObserver}
 */
export function setIntersectionObserver (element, callback) {
    const options = {
        root: null,
        rootMargin: '0px'
    };
    const observer = new window.IntersectionObserver(entries => {
        const entry = entries[0];
        if (entry.isIntersecting) {
            observer.unobserve(entry.target);
            callback();
        }
    }, options);
    observer.observe(element);
    return observer;
}

/**
 * Convert the string from a data-behavior-props attribute to an usable object.
 *
 * @param {String} dataBehaviorPropsAttribute utf-8 encoded JSON string
 * @returns {Object} object containing props for a Behavior to store in the
 *                   html_field value of a field
 */
export function decodeDataBehaviorProps(dataBehaviorPropsAttribute) {
    return JSON.parse(decodeURIComponent(dataBehaviorPropsAttribute));
}

/**
 * Convert an object destined to be used as the value of a data-behavior-props
 * attribute to an utf-8 encoded JSON string (so that there is no special
 * character that would be sanitized by i.e. DOMPurify).
 *
 * @param {Object} dataBehaviorPropsObject object containing props for a
 *                 Behavior to store in the html_field value of a field
 * @returns {String} utf-8 encoded JSON string
 */
export function encodeDataBehaviorProps(dataBehaviorPropsObject) {
    return encodeURIComponent(JSON.stringify(dataBehaviorPropsObject));
}
