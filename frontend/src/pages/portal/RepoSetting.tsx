import React, { useEffect, useRef, useState } from 'react';
import { Form, Button, Alert } from 'react-bootstrap';
import { GFIRepoBasicProp } from '../main/GFIRepoDisplayView';

import '../../style/gfiStyle.css';
import { GFIAlarm } from '../GFIComponents';
import { deleteRepoQuery } from '../../api/api';

export type RepoSettingPops = GFIRepoBasicProp;

export function RepoSetting(props: RepoSettingPops) {
  const { repoInfo } = props;

  const gfiThresholdRef = useRef<HTMLInputElement>(null);
  const gfiTagNameRef = useRef<HTMLInputElement>(null);
  const [showComment, setShowComment] = useState<boolean>(false);
  const [newcomerThresholdSelected, setNewcomerThresholdSelected] = useState(1);
  const [showDeleteAlarm, setShowDeleteAlarm] = useState(false);

  const onBotConfigSubmit = () => {
    console.log(gfiThresholdRef.current?.value);
    console.log(newcomerThresholdSelected);
    console.log(showComment);
  };

  const deleteRepo = () => {
    deleteRepoQuery(repoInfo.name, repoInfo.owner).then(() => {
      setShowDeleteAlarm(false);
      window.location.reload();
    });
  };

  return (
    <div className="gfi-repo-setting-container flex-col flex-wrap align-items-stretch">
      <div className="gfi-repo-setting-item-container">
        <div className="gfi-repo-setting-item-title">GFI-Bot Settings</div>
        <div className="gfi-repo-setting-item flex-col">
          <Form className="flex-col">
            <div className="flex-row justify-content-between align-items-start flex-wrap">
              <div className="gfi-repo-setting-form-col">
                <Form.Group controlId="gfi-threshold">
                  <Form.Label className="gfi-repo-setting-form-label">
                    GFI Threshold
                  </Form.Label>
                  <Form.Control placeholder="0.5" ref={gfiThresholdRef} />
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
                    <option> 1 </option>
                    <option> 2 </option>
                    <option> 3 </option>
                    <option> 4 </option>
                    <option> 5 </option>
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
                    placeholder="good first issue"
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
        </div>
      </div>
      <div className="flex-row gfi-repo-setting-btns">
        <Button variant="outline-success" size="sm">
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
