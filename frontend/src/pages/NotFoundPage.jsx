import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { Card, EmptyState } from '../components';

export function NotFoundPage() {
  return (
    <div className="page-wrapper flex-center" style={{ minHeight: '60vh' }}>
      <Card style={{ maxWidth: 500, width: '100%', textAlign: 'center' }}>
        <EmptyState
          icon={AlertCircle}
          title="Page Not Found (404)"
          description="The requested dashboard view or machine resource does not exist."
          action={
            <Link to="/" className="btn btn-primary">
              <ArrowLeft size={16} />
              <span>Return to Overview</span>
            </Link>
          }
        />
      </Card>
    </div>
  );
}

export default NotFoundPage;
