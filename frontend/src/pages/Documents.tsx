import React from 'react';
import { Box, Typography, Card, CardContent, Button } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';

const Documents: React.FC = () => {
  const columns = [
    { field: 'name', headerName: 'Document Name', width: 300 },
    { field: 'type', headerName: 'Type', width: 150 },
    { field: 'uploadDate', headerName: 'Upload Date', width: 150 },
    { field: 'status', headerName: 'Status', width: 120 },
  ];

  const rows = [
    { id: 1, name: 'GDPR Compliance Manual.pdf', type: 'Policy', uploadDate: '2024-01-15', status: 'Processed' },
    { id: 2, name: 'SOX Audit Report Q4.docx', type: 'Report', uploadDate: '2024-01-14', status: 'Processing' },
    { id: 3, name: 'Data Protection Policy v2.pdf', type: 'Policy', uploadDate: '2024-01-13', status: 'Processed' },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Document Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Upload and manage compliance documents
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<CloudUpload />}>
          Upload Document
        </Button>
      </Box>

      <Card>
        <CardContent>
          <Box sx={{ height: 400, width: '100%' }}>
            <DataGrid
              rows={rows}
              columns={columns}
              initialState={{
                pagination: {
                  paginationModel: { pageSize: 10, page: 0 }
                }
              }}
              pageSizeOptions={[10]}
              checkboxSelection
              disableRowSelectionOnClick
            />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Documents;