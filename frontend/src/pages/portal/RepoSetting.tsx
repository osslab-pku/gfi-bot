import React, { useEffect, useRef, useState } from 'react';
import { Form, Button } from 'react-bootstrap';
import { GFIRepoBasicProp } from '../main/GFIRepoDisplayView';

import '../../style/gfiStyle.css';
import { GFIAlarm, GFIAlarmPanelVariants } from '../GFIComponents';
import {
  deleteRepoQuery,
  getRepoConfig,
  updateRepoConfig,
  updateRepoInfo,
} from '../../api/api';
import type { RepoGFIConfig } from '../../model/api';
import { checkIsNumber } from '../../utils';

export type RepoSettingPops = GFIRepoBasicProp;

export function RepoSetting(props: RepoSettingPops) {
  const { repoInfo } = props;

  const gfiThresholdRef = useRef<HTMLInputElement>(null);
  const gfiTagNameRef = useRef<HTMLInputElement>(null);
  const [showUpdateBanner, setShowUpdateBanner] = useState(false);
  const [showComment, setShowComment] = useState(false);
  const [newcomerThresholdSelected, setNewcomerThresholdSelected] = useState(1);
  const [showDeleteAlarm, setShowDeleteAlarm] = useState(false);
  const [currentRepoConfig, setCurrentRepoConfig] = useState<RepoGFIConfig>();
  const [showConfigAlarmBanner, setShowConfigAlarmBanner] = useState(false);
  const [configAlarmBanner, setConfigAlarmBanner] = useState<{
    variant: GFIAlarmPanelVariants;
    title: string;
  }>({
    variant: 'danger',
    title: '',
  });

  const loadRepoConfig = () => {
    getRepoConfig(repoInfo.name, repoInfo.owner).then((config) => {
      if (config) {
        setCurrentRepoConfig(config);
      }
    });
  };

  useEffect(() => {
    loadRepoConfig();
  }, []);

  useEffect(() => {
    if (currentRepoConfig) {
      setShowComment(currentRepoConfig.need_comment);
      setNewcomerThresholdSelected(currentRepoConfig.newcomer_threshold);
    }
  }, [currentRepoConfig]);

  const onBotConfigSubmit = () => {
    if (gfiThresholdRef.current && gfiTagNameRef.current) {
      let gfiThreshold = gfiThresholdRef.current.value;
      if (!gfiThreshold && currentRepoConfig) {
        gfiThreshold = currentRepoConfig.gfi_threshold.toString();
      }
      let gfiTag = gfiTagNameRef.current.value;
      if (!gfiTag && currentRepoConfig) {
        gfiTag = currentRepoConfig.issue_tag;
      }
      if (
        checkIsNumber(gfiThreshold) &&
        parseFloat(gfiThreshold) > 0 &&
        parseFloat(gfiThreshold) < 1 &&
        gfiTag
      ) {
        const repoConfig: RepoGFIConfig = {
          newcomer_threshold: newcomerThresholdSelected,
          issue_tag: gfiTag,
          gfi_threshold: parseFloat(gfiThreshold),
          need_comment: showComment,
        };
        updateRepoConfig(repoInfo.name, repoInfo.owner, repoConfig).then(
          (res) => {
            if (res === 'success') {
              setShowConfigAlarmBanner(true);
              setConfigAlarmBanner({
                variant: 'success',
                title: 'Repo config successfully updated!',
              });
            } else {
              setShowConfigAlarmBanner(true);
              setConfigAlarmBanner({
                variant: 'danger',
                title: 'Repo config update failed',
              });
            }
            loadRepoConfig();
          }
        );
      } else {
        setShowConfigAlarmBanner(true);
        setConfigAlarmBanner({
          variant: 'danger',
          title: 'Please input a GFI threshold between 0 and 1.',
        });
      }
    }
  };

  const deleteRepo = () => {
    deleteRepoQuery(repoInfo.name, repoInfo.owner).then(() => {
      setShowDeleteAlarm(false);
      window.location.reload();
    });
  };

  const updateGFIInfo = () => {
    updateRepoInfo(repoInfo.name, repoInfo.owner).then((res) => {
      setShowUpdateBanner(true);
    });
  };

  return (
    <div className="gfi-repo-setting-container flex-col flex-wrap align-items-stretch">
      <div style={{ margin: '0 1rem' }}>
        {showUpdateBanner && (
          <GFIAlarm
            variant="success"
            title={`Updating ${repoInfo.owner} / ${repoInfo.name}, we'll send you an email after successfully updated `}
            onClose={() => setShowUpdateBanner(false)}
          />
        )}
      </div>

      <div style={{ margin: '0 1rem' }}>
        {showConfigAlarmBanner && (
          <GFIAlarm
            variant={configAlarmBanner.variant}
            title={configAlarmBanner.title}
            onClose={() => setShowConfigAlarmBanner(false)}
          />
        )}
      </div>

      <div className="gfi-repo-setting-item-container">
        <div className="gfi-repo-setting-item-title">GFI-Bot Settings</div>
        <div className="gfi-repo-setting-item flex-col">
          {currentRepoConfig && (
            <Form className="flex-col">
              <div className="flex-row justify-content-between align-items-start flex-wrap">
                <div className="gfi-repo-setting-form-col">
                  <Form.Group controlId="gfi-threshold">
                    <Form.Label className="gfi-repo-setting-form-label">
                      GFI Threshold
                    </Form.Label>
                    <Form.Control
                      placeholder={currentRepoConfig.gfi_threshold.toString()}
                      ref={gfiThresholdRef}
                    />
                    <Form.Text className="text-muted">
                      Threshold for issue labeled as a GFI.
                    </Form.Text>
                  </Form.Group>
                </div>
                <div className="gfi-repo-setting-form-col">
                  <Form.Group controlId="newcomer-threshold">
                    <Form.Label className="gfi-repo-setting-form-label">
                      Newcomer Threshold
                    </Form.Label>
                    <Form.Select
                      onChange={(e) => {
                        setNewcomerThresholdSelected(parseInt(e.target.value));
                      }}
                    >
                      {[0, 1, 2, 3, 4].map((i, idx) => (
                        <option
                          selected={idx + 1 === newcomerThresholdSelected}
                        >
                          {i + 1}
                        </option>
                      ))}
                    </Form.Select>
                    <Form.Text className="text-muted">
                      Max commits as a newcomer.
                    </Form.Text>
                  </Form.Group>
                </div>
                <div className="gfi-repo-setting-form-col">
                  <Form.Group controlId="gfi-tag-name">
                    <Form.Label className="gfi-repo-setting-form-label">
                      Issue Tag Name
                    </Form.Label>
                    <Form.Control
                      placeholder={currentRepoConfig.issue_tag}
                      ref={gfiTagNameRef}
                    />
                    <Form.Text className="text-muted">
                      Issue Tag for GFIs
                    </Form.Text>
                  </Form.Group>
                </div>
              </div>
              <div className="gfi-repo-setting-form-col">
                <Form.Group controlId="gfi-tag-name">
                  <Form.Check
                    checked={showComment}
                    onChange={() => setShowComment(!showComment)}
                    label="Need comments for GFIs"
                  />
                </Form.Group>
              </div>
              <Button
                style={{ marginLeft: 'auto' }}
                size="sm"
                variant="outline-primary"
                onClick={() => {
                  onBotConfigSubmit();
                }}
              >
                {' '}
                Submit{' '}
              </Button>
            </Form>
          )}
        </div>
      </div>
      <div className="flex-row gfi-repo-setting-btns">
        <Button
          variant="outline-success"
          size="sm"
          onClick={() => {
            updateGFIInfo();
          }}
        >
          Update GFI Info
        </Button>
        <Button
          variant="outline-danger"
          size="sm"
          onClick={() => {
            if (!showDeleteAlarm) {
              setShowDeleteAlarm(true);
            }
          }}
        >
          Delete Repo
        </Button>
      </div>
      <div className="flex-row gfi-repo-setting-btns">
        {showDeleteAlarm && (
          <GFIAlarm className="no-btn gfi-repo-setting-alarm">
            <div>
              {' '}
              Warning: You're going to delete your repository in GFI-Bot{' '}
            </div>
            <div className="flex-row gfi-repo-setting-alarm-btns">
              <Button
                className="gfi-repo-setting-alarm-btn"
                variant="outline-success"
                size="sm"
                onClick={() => setShowDeleteAlarm(false)}
              >
                {' '}
                Dismiss{' '}
              </Button>
              <Button
                className="gfi-repo-setting-alarm-btn"
                variant="outline-danger"
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  deleteRepo();
                }}
              >
                {' '}
                Continue{' '}
              </Button>
            </div>
          </GFIAlarm>
        )}
      </div>
    </div>
  );
}
