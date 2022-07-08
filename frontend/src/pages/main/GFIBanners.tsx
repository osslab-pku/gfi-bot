import React, { forwardRef, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

export function GFIAlphaWarning() {
  return (
    <div className="kanban wrapper">
      <div
        className="gfi-wrapper tags"
        style={{ backgroundColor: 'rgba(255, 91, 91, 0.2)' }}
      >
        <div style={{ marginBottom: '0.3rem' }}>Warning</div>
        <div className="tags wrapper" style={{ marginBottom: '0.1rem' }}>
          GFI-Bot is undergoing rapid development and still highly unstable. It
          is not recommended to use it in production.
        </div>
      </div>
    </div>
  );
}
