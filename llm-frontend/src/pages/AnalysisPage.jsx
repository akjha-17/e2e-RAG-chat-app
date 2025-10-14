import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Rating,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Star as StarIcon,
  BarChart as BarChartIcon,
  Timeline as TimelineIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { getFeedbacks } from '../api';
import { useAuth } from '../context/AuthContext';

// Utility functions for date formatting
const formatDateForDisplay = (utcTimestamp) => {
  if (!utcTimestamp) return 'N/A';
  const date = new Date(utcTimestamp + 'Z');
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

const formatTimeForDisplay = (utcTimestamp) => {
  if (!utcTimestamp) return 'N/A';
  const date = new Date(utcTimestamp + 'Z');
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
};

const formatDateForCSV = (utcTimestamp) => {
  if (!utcTimestamp) return '';
  const date = new Date(utcTimestamp + 'Z');
  // Use ISO date format (YYYY-MM-DD) for better CSV compatibility
  return date.getFullYear() + '-' + 
         String(date.getMonth() + 1).padStart(2, '0') + '-' + 
         String(date.getDate()).padStart(2, '0');
};

const formatTimeForCSV = (utcTimestamp) => {
  if (!utcTimestamp) return '';
  const date = new Date(utcTimestamp + 'Z');
  // Use 24-hour format (HH:MM:SS) for better CSV compatibility
  return String(date.getHours()).padStart(2, '0') + ':' + 
         String(date.getMinutes()).padStart(2, '0') + ':' + 
         String(date.getSeconds()).padStart(2, '0');
};

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

export default function AnalysisPage() {
  const { token, isAdmin } = useAuth();
  const theme = useTheme();
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [chartDialogOpen, setChartDialogOpen] = useState(false);
  const [chartType, setChartType] = useState('');

  useEffect(() => {
    if (isAdmin()) {
      fetchFeedbacks();
    } else {
      setError('Admin privileges required to view analytics');
      setLoading(false);
    }
  }, [token]);

  const fetchFeedbacks = async () => {
    try {
      setLoading(true);
      const response = await getFeedbacks(token);
      // Ensure we have data structure we expect
      const feedbackData = Array.isArray(response.data) ? response.data : [];
      setFeedbacks(feedbackData);
      setError(''); // Clear any previous errors
    } catch (err) {
      setError('Failed to load feedback data. Please check your admin permissions.');
      setFeedbacks([]); // Set empty array on error
      console.error('Error fetching feedbacks:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate statistics
  const stats = {
    totalFeedbacks: feedbacks.length,
    averageRating: feedbacks.length > 0 
      ? (feedbacks.reduce((sum, fb) => sum + (fb.rating || 0), 0) / feedbacks.filter(fb => fb.rating).length).toFixed(1)
      : 0,
    ratingDistribution: {
      5: feedbacks.filter(fb => fb.rating === 5).length,
      4: feedbacks.filter(fb => fb.rating === 4).length,  // Thumbs up from chat
      3: feedbacks.filter(fb => fb.rating === 3).length,
      2: feedbacks.filter(fb => fb.rating === 2).length,  // Thumbs down from chat
      1: feedbacks.filter(fb => fb.rating === 1).length,
    },
    withComments: feedbacks.filter(fb => fb.comment && fb.comment.trim()).length,
    // Additional stats for thumbs vs stars
    thumbsUp: feedbacks.filter(fb => fb.rating === 4 && fb.session_id && fb.session_id.includes('chat')).length,
    thumbsDown: feedbacks.filter(fb => fb.rating === 2 && fb.session_id && fb.session_id.includes('chat')).length,
    starRatings: feedbacks.filter(fb => [1, 3, 5].includes(fb.rating) || (fb.session_id && fb.session_id.includes('general_feedback'))).length
  };

  const getRatingColor = (rating) => {
    if (rating >= 4) return 'success';
    if (rating >= 3) return 'warning';
    return 'error';
  };

  // Chart data preparation functions
  const getRatingChartData = () => {
    const labels = ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'];
    const data = [
      stats.ratingDistribution[1],
      stats.ratingDistribution[2],
      stats.ratingDistribution[3],
      stats.ratingDistribution[4],
      stats.ratingDistribution[5]
    ];
    
    return {
      labels,
      datasets: [
        {
          label: 'Number of Ratings',
          data,
          backgroundColor: [
            'rgba(244, 67, 54, 0.8)',  // Red for 1 star
            'rgba(255, 152, 0, 0.8)',  // Orange for 2 stars  
            'rgba(255, 193, 7, 0.8)',  // Yellow for 3 stars
            'rgba(139, 195, 74, 0.8)', // Light green for 4 stars
            'rgba(76, 175, 80, 0.8)'   // Green for 5 stars
          ],
          borderColor: [
            'rgba(244, 67, 54, 1)',
            'rgba(255, 152, 0, 1)',
            'rgba(255, 193, 7, 1)',
            'rgba(139, 195, 74, 1)',
            'rgba(76, 175, 80, 1)'
          ],
          borderWidth: 1
        }
      ]
    };
  };

  const getTimelineChartData = () => {
    if (feedbacks.length === 0) return { labels: [], datasets: [] };

    // Group feedbacks by date and calculate average rating
    // Convert UTC timestamp to local date for grouping
    const dateRatings = {};
    feedbacks.forEach(fb => {
      if (fb.rating && fb.timestamp) {
        // Convert UTC timestamp to local date by adding 'Z' to ensure proper UTC parsing
        const utcDate = new Date(fb.timestamp + 'Z');
        const dateKey = utcDate.toISOString().split('T')[0]; // Use ISO date format for sorting
        
        if (!dateRatings[dateKey]) {
          dateRatings[dateKey] = { sum: 0, count: 0 };
        }
        dateRatings[dateKey].sum += fb.rating;
        dateRatings[dateKey].count += 1;
      }
    });

    if (Object.keys(dateRatings).length === 0) {
      return { labels: [], datasets: [] };
    }

    // Sort dates and add padding
    const sortedDates = Object.keys(dateRatings).sort();
    const earliestDate = new Date(sortedDates[0]);
    const latestDate = new Date(sortedDates[sortedDates.length - 1]);
    
    // Add 2 days padding before the earliest date
    const paddingStart = new Date(earliestDate);
    paddingStart.setDate(paddingStart.getDate() - 2);
    
    // Add 1 day padding after the latest date  
    const paddingEnd = new Date(latestDate);
    paddingEnd.setDate(paddingEnd.getDate() + 1);
    
    // Generate complete date range with padding
    const allDates = [];
    const allRatings = [];
    
    for (let d = new Date(paddingStart); d <= paddingEnd; d.setDate(d.getDate() + 1)) {
      const dateKey = d.toISOString().split('T')[0];
      const displayDate = d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric'
      });
      
      allDates.push(displayDate);
      
      if (dateRatings[dateKey]) {
        allRatings.push((dateRatings[dateKey].sum / dateRatings[dateKey].count).toFixed(1));
      } else {
        allRatings.push(null); // No data for this date
      }
    }

    return {
      labels: allDates,
      datasets: [
        {
          label: 'Average Rating',
          data: allRatings,
          borderColor: theme.palette.primary.main,
          backgroundColor: theme.palette.mode === 'dark' 
            ? 'rgba(144, 202, 249, 0.1)' 
            : 'rgba(33, 150, 243, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          spanGaps: true // Connect points even with null values
        }
      ]
    };
  };

  // Chart options
  const barChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: theme.palette.text.primary
        }
      },
      title: {
        display: true,
        text: 'Feedback Ratings Distribution',
        color: theme.palette.text.primary
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Rating Categories',
          color: theme.palette.text.primary
        },
        ticks: {
          color: theme.palette.text.secondary
        },
        grid: {
          color: theme.palette.divider
        }
      },
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          color: theme.palette.text.secondary
        },
        title: {
          display: true,
          text: 'Number of Feedbacks',
          color: theme.palette.text.primary
        },
        grid: {
          color: theme.palette.divider
        }
      }
    }
  };

  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: theme.palette.text.primary
        }
      },
      title: {
        display: true,
        text: 'Average Rating Over Time',
        color: theme.palette.text.primary
      }
    },
    scales: {
      x: {
        ticks: {
          maxRotation: 45,
          minRotation: 0,
          color: theme.palette.text.secondary
        },
        title: {
          display: true,
          text: 'Date',
          color: theme.palette.text.primary
        },
        grid: {
          color: theme.palette.divider
        }
      },
      y: {
        beginAtZero: true,
        max: 5,
        ticks: {
          stepSize: 0.5,
          color: theme.palette.text.secondary
        },
        title: {
          display: true,
          text: 'Average Rating (1-5)',
          color: theme.palette.text.primary
        },
        grid: {
          color: theme.palette.divider
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index'
    },
    elements: {
      point: {
        radius: 4,
        hoverRadius: 6
      }
    }
  };

  // Export to CSV function
  const exportToCSV = () => {
    if (feedbacks.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = ['Date', 'Time', 'Username', 'Query', 'Rating', 'Comment'];
    const csvData = feedbacks.map(fb => {
      return [
        formatDateForCSV(fb.timestamp),
        formatTimeForCSV(fb.timestamp),
        fb.username || 'Anonymous',
        (fb.query || '').replace(/"/g, '""'), // Escape quotes
        fb.rating || '',
        (fb.comment || '').replace(/"/g, '""') // Escape quotes
      ];
    });

    // Create CSV content without quotes around date/time for better Excel compatibility
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => {
        return row.map((field, index) => {
          // Don't quote date/time fields (first two columns), quote others that might contain commas
          if (index === 0 || index === 1 || index === 4) { // Date, Time, Rating
            return field;
          } else {
            return `"${field}"`; // Quote other fields
          }
        }).join(',');
      })
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `feedbacks_export_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const openChart = (type) => {
    setChartType(type);
    setChartDialogOpen(true);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 2 }}>
          <AnalyticsIcon sx={{ fontSize: 'inherit', color: 'primary.main' }} />
          Feedback Analysis
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Analyze user feedback and ratings to improve AI responses
        </Typography>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress size={40} />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <>
          {/* Action Buttons */}
          <Card elevation={2} sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                Analysis Tools
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<BarChartIcon />}
                  onClick={() => openChart('ratings')}
                  sx={{ py: 1.5, height: 56, flex: '1 1 300px', maxWidth: '32%' }}
                >
                  View Rating Distribution
                </Button>
                <Button
                  variant="contained"
                  startIcon={<TimelineIcon />}
                  onClick={() => openChart('timeline')}
                  sx={{ py: 1.5, height: 56, flex: '1 1 300px', maxWidth: '32%' }}
                >
                  View Rating Timeline
                </Button>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={exportToCSV}
                  sx={{ py: 1.5, height: 56, flex: '1 1 300px', maxWidth: '32%' }}
                  color="success"
                >
                  Export to CSV
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Statistics Cards */}
          <Card elevation={2} sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                Statistics Overview
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '23%' }}>
                  <PeopleIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1, mx: 'auto' }} />
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    {stats.totalFeedbacks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Feedbacks
                  </Typography>
                </Box>

                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '23%' }}>
                  <StarIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1, mx: 'auto' }} />
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    {stats.averageRating}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Rating
                  </Typography>
                </Box>

                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '23%' }}>
                  <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main', mb: 1, mx: 'auto' }} />
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {((stats.ratingDistribution[4] + stats.ratingDistribution[5]) / stats.totalFeedbacks * 100).toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Positive (4-5★)
                  </Typography>
                </Box>

                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '23%' }}>
                  <AnalyticsIcon sx={{ fontSize: 40, color: 'info.main', mb: 1, mx: 'auto' }} />
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.main' }}>
                    {stats.withComments}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    With Comments
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Feedback Types Breakdown */}
          <Card elevation={2} sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                Feedback Types
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '32%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <Typography variant="body1" sx={{ mr: 1, fontSize: '2rem' }}>👍</Typography>
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {stats.ratingDistribution[4]}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Chat Thumbs Up
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '32%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <Typography variant="body1" sx={{ mr: 1, fontSize: '2rem' }}>👎</Typography>
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'error.main' }}>
                    {stats.ratingDistribution[2]}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Chat Thumbs Down
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 200px', maxWidth: '32%' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                    <StarIcon sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    {stats.ratingDistribution[1] + stats.ratingDistribution[3] + stats.ratingDistribution[5]}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Star Ratings
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Rating Distribution */}
          <Card elevation={2} sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                Rating Distribution (All Feedback)
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
                {[5, 4, 3, 2, 1].map((rating) => (
                  <Box key={rating} sx={{ textAlign: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 2, height: '120px', display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: '1 1 150px', maxWidth: '18%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                      <Typography variant="body1" sx={{ mr: 1 }}>{rating}</Typography>
                      {rating === 4 ? <Typography sx={{ fontSize: '1.2rem' }}>👍</Typography> : 
                       rating === 2 ? <Typography sx={{ fontSize: '1.2rem' }}>👎</Typography> :
                       <StarIcon sx={{ fontSize: 20, color: 'warning.main' }} />}
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 600, color: getRatingColor(rating) + '.main' }}>
                      {stats.ratingDistribution[rating]}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ({stats.totalFeedbacks > 0 ? (stats.ratingDistribution[rating] / stats.totalFeedbacks * 100).toFixed(1) : 0}%)
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Feedback Table */}
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Recent Feedback Details
              </Typography>
              {feedbacks.length === 0 ? (
                <Alert severity="info">
                  No feedback data available yet. Users need to submit feedback on AI responses.
                </Alert>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                        <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>User</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Question</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Rating</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Comment</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {feedbacks.slice().reverse().map((feedback, index) => (
                        <TableRow key={index} sx={{ '&:hover': { backgroundColor: '#f9f9f9' } }}>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDateForDisplay(feedback.timestamp)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatTimeForDisplay(feedback.timestamp)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={feedback.username || 'Anonymous'} 
                              size="small" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell sx={{ maxWidth: 300 }}>
                            <Typography variant="body2" sx={{ 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              {feedback.query || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {feedback.rating ? (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Rating value={feedback.rating} readOnly size="small" />
                                <Typography variant="body2" color="text.secondary">
                                  ({feedback.rating}/5)
                                </Typography>
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                No rating
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell sx={{ maxWidth: 250 }}>
                            {feedback.comment ? (
                              <Typography variant="body2" sx={{ 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}>
                                {feedback.comment}
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                No comment
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Chart Dialog */}
      <Dialog 
        open={chartDialogOpen} 
        onClose={() => setChartDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {chartType === 'ratings' ? 'Feedback Ratings Distribution' : 'Average Rating Over Time'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ height: 400, p: 2 }}>
            {chartType === 'ratings' ? (
              <Bar data={getRatingChartData()} options={barChartOptions} />
            ) : chartType === 'timeline' ? (
              <Line data={getTimelineChartData()} options={lineChartOptions} />
            ) : null}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChartDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}