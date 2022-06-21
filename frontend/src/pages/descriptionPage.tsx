import React from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../style/gfiStyle.css';
import { defaultFontFamily } from '../utils';

import { Link } from 'react-router-dom';

// TODO: @MSKYurina
//       Design and Animation

const SELF_INTRO =
  'The introduction of the bot is submitted to FSE 2022 Demo --- GFI-Bot: Automated Good First Issue Recommendation on GitHub';

const GFIBOT_INTRO =
  "The embedded ML approach is introduced in the following paper: W. Xiao, H. He, W. Xu, X. Tan, J. Dong, M. Zhou. Recommending Good First Issues in GitHub OSS Projects. Accepted at ICSE'2022.";

export const DescriptionPage: React.FC = () => {
  const welcomeMsg = 'GFI-BOT WebApp';
  const description =
    'ML-powered 🤖 for finding and labeling Good First Issues in your GitHub project!';

  return (
    <div className="scrollbar-hidden">
      <Container
        className="flex-col flex-center"
        style={{
          marginTop: '9%',
        }}
      >
        <Row style={{ height: '25%', flexDirection: 'column-reverse' }}>
          <Col sm={12}>
            <Row style={{ marginTop: 'auto' }}>
              <Col
                style={{
                  textAlign: 'center',
                  fontWeight: 'bolder',
                  fontSize: 'xx-large',
                }}
              >
                {welcomeMsg}
              </Col>
            </Row>
          </Col>
        </Row>
        <Row style={{ marginTop: '20px' }}>
          <Col style={{ textAlign: 'center', maxWidth: '400px' }}>
            {description}
          </Col>
        </Row>
        <Row style={{ margin: '35px' }}>
          <Col className="flex-col flex-center description-container">
            <div style={{ maxWidth: '600px' }}>{SELF_INTRO}</div>
            <div style={{ maxWidth: '600px' }}>{GFIBOT_INTRO}</div>
            <Link to="/">
              <Button variant="outline-primary" style={{ marginTop: '2rem' }}>
                {' '}
                Get Started{' '}
              </Button>
            </Link>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

interface DescriptionPageProps {
  title?: string;
  content?: string;
}

function Description(props: DescriptionPageProps) {
  return (
    <Container>
      <Row
        style={{
          fontFamily: defaultFontFamily,
          fontSize: '24px',
          color: '#6d6d6d',
          fontWeight: '300',
        }}
      >
        <Col>{props.title}</Col>
      </Row>
      <Row
        style={{
          fontFamily: defaultFontFamily,
          fontSize: '17px',
          fontWeight: '400',
          marginTop: '10px',
        }}
      >
        <Col>{props.content}</Col>
      </Row>
    </Container>
  );
}
