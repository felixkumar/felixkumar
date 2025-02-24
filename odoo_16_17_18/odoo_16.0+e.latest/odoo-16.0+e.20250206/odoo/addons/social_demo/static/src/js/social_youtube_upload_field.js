/** @odoo-module **/

import { YoutubeUploadField } from '@social_youtube/js/social_youtube_upload_field';

import { patch } from '@web/core/utils/patch';

patch(YoutubeUploadField.prototype, 'social_demo.YoutubeUploadField', {

    /**
     * When the user selects a file, as we are in demo mode, the video will not be uploaded.
     * Display a toaster to the user to inform them cannot upload video in demo mode.
     *
     * @param {Event} e
     * @private
     */
    async _onFileChanged(e) {
        this.notification.add(this.env._t('You cannot upload videos in demo mode.'), {
            type: 'info',
        });
    }
});
