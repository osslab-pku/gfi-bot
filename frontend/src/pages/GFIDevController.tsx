import React, { useCallback, useRef, useState } from 'react';
import { SettingOutlined, ReloadOutlined } from '@ant-design/icons';
import { GFIAlarm, GFIOverlay } from './GFIComponents';
import '../style/gfiStyle.css';
import { useIsMobile } from './app/windowContext';
import { Button, Form } from 'react-bootstrap';

import { getBaseURL, URL_KEY } from '../api/query';
import { checkIsValidUrl } from '../utils';

export function GFIDevController() {
  const overlayRef = useRef<HTMLDivElement>(null);
  const [hideOverlay, setHideOverlay] = useState(true);

  const [showAlarmBanner, setShowAlarmBanner] = useState(false);
  const [alarmBannerTitle, setAlarmBannerTitle] = useState('');

  const [showUpdateBanner, setShowUpdateBanner] = useState(false);
  const [updateBannerTitle, setUpdateBannerTitle] = useState('');
  const isMobile = useIsMobile();

  const [shouldDisableURLBtn, setShouldDisableURLBtn] = useState(true);
  const [showRefreshBtn, setShowRefreshBtn] = useState(false);

  const baseURLRef = useRef<HTMLInputElement | null>(null);

  const urlRef = useCallback((node: HTMLInputElement | null) => {
    baseURLRef.current = node;
  }, []);

  const modifyBaseURL = useCallback(() => {
    if (baseURLRef && baseURLRef.current) {
      const nxtBaseURL = baseURLRef.current.value || '';
      if (checkIsValidUrl(nxtBaseURL)) {
        localStorage.setItem(URL_KEY, nxtBaseURL);
        setShowUpdateBanner(true);
        setShowRefreshBtn(true);
        setUpdateBannerTitle('Base URL successfully modified!');
      }
    } else {
      setShowAlarmBanner(true);
      setAlarmBannerTitle('You should enter a correct URL!');
      setShowRefreshBtn(false);
    }
  }, []);

  return (
    <div className="gfi-dev-controller flex-row">
      <GFIOverlay
        className="gfi-dev-controller-overlay"
        id="gfi-dev-controller-overlay"
        direction="right"
        width={isMobile ? '80%' : '40%'}
        hidden={hideOverlay}
        ref={overlayRef}
        callback={() => {
          setHideOverlay(true);
        }}
        animation
      >
        <div className="gfi-repo-setting-item-title" id={'dev-setting-title'}>
          GFI-Bot Dev Environment Settings
        </div>
        <div className="gfi-repo-setting-item-container" id={'dev-setting'}>
          {showUpdateBanner && (
            <GFIAlarm
              variant="success"
              title={updateBannerTitle}
              onClose={() => setShowUpdateBanner(false)}
            />
          )}
          {showAlarmBanner && (
            <GFIAlarm
              variant="danger"
              title={alarmBannerTitle}
              onClose={() => setShowAlarmBanner(false)}
            />
          )}
          <Form className={'dev-setting-form'}>
            <Form.Group controlId="base-url">
              <Form.Label className="gfi-repo-setting-form-label">
                Modify Base URL
              </Form.Label>
              <div className="flex-row">
                <Form.Control
                  ref={urlRef}
                  placeholder={getBaseURL()}
                  style={{
                    borderBottomRightRadius: '0',
                    borderTopRightRadius: '0',
                  }}
                  onChange={(event) => {
                    if (event.target.value.length) {
                      setShouldDisableURLBtn(false);
                    } else {
                      setShouldDisableURLBtn(true);
                    }
                  }}
                />
                <Button
                  variant="outline-success"
                  style={{
                    borderBottomLeftRadius: '0',
                    borderTopLeftRadius: '0',
                  }}
                  onClick={() => {
                    modifyBaseURL();
                  }}
                  disabled={shouldDisableURLBtn}
                >
                  Change
                </Button>
              </div>
              {showRefreshBtn && (
                <button
                  className="flex-row dev-setting-refresh-btn flex-center"
                  onClick={() => {
                    window.location.reload();
                  }}
                >
                  <ReloadOutlined
                    style={{
                      fontSize: '12px',
                    }}
                  />
                  <div
                    style={{
                      textDecoration: 'underline',
                      marginLeft: '0.2rem',
                      fontSize: '0.9rem',
                    }}
                  >
                    {' '}
                    Refresh{' '}
                  </div>
                </button>
              )}
            </Form.Group>
          </Form>
        </div>
      </GFIOverlay>
      <button
        className="gfi-dev-controller-btn"
        onClick={() => {
          setHideOverlay(false);
        }}
      >
        <SettingOutlined
          style={{
            fontSize: '17px',
            color: 'darkgray',
          }}
        />
        <div className="gfi-dev-controller-title">Dev Environment Settings</div>
      </button>
    </div>
  );
}
