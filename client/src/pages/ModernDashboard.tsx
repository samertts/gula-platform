import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from "recharts";
import { 
  Users, Beaker, FileText, TrendingUp, Clock, AlertCircle,
  CheckCircle, Activity, Download, Plus
} from "lucide-react";
import { motion } from "framer-motion";

// Sample data
const patientData = [
  { name: "Mon", patients: 24, samples: 12 },
  { name: "Tue", patients: 28, samples: 15 },
  { name: "Wed", patients: 32, samples: 18 },
  { name: "Thu", patients: 26, samples: 14 },
  { name: "Fri", patients: 35, samples: 22 },
  { name: "Sat", patients: 20, samples: 10 },
  { name: "Sun", patients: 18, samples: 8 },
];

const sampleStatusData = [
  { name: "Completed", value: 65, fill: "#10b981" },
  { name: "Pending", value: 25, fill: "#f59e0b" },
  { name: "Failed", value: 10, fill: "#ef4444" },
];

const StatCard = ({ icon: Icon, title, value, change, color }: any) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
            <p className="text-3xl font-bold mt-2">{value}</p>
            <p className={`text-sm mt-2 ${change > 0 ? "text-green-600" : "text-red-600"}`}>
              {change > 0 ? "↑" : "↓"} {Math.abs(change)}% from last week
            </p>
          </div>
          <div className={`p-3 rounded-lg ${color}`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

export default function ModernDashboard() {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">Welcome to GULA Platform</h1>
          <p className="text-gray-600 mb-6">Please log in to access the dashboard</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.name || "User"}! 👋
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Here's what's happening with your laboratory today
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          icon={Users} 
          title="Total Patients" 
          value="1,234" 
          change={12}
          color="bg-blue-500"
        />
        <StatCard 
          icon={Beaker} 
          title="Samples Today" 
          value="87" 
          change={8}
          color="bg-purple-500"
        />
        <StatCard 
          icon={FileText} 
          title="Reports Pending" 
          value="23" 
          change={-5}
          color="bg-orange-500"
        />
        <StatCard 
          icon={CheckCircle} 
          title="Completed Tests" 
          value="456" 
          change={15}
          color="bg-green-500"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Line Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle>Patient & Sample Trends</CardTitle>
              <CardDescription>Weekly activity overview</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={patientData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="patients" stroke="#3b82f6" strokeWidth={2} />
                  <Line type="monotone" dataKey="samples" stroke="#8b5cf6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Pie Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Sample Status</CardTitle>
              <CardDescription>Distribution</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={sampleStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {sampleStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button className="w-full justify-start" variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                Register New Patient
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Beaker className="w-4 h-4 mr-2" />
                Add Sample
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <FileText className="w-4 h-4 mr-2" />
                Generate Report
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Download Data
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { icon: CheckCircle, text: "Sample #S001 completed", time: "2 hours ago", color: "text-green-600" },
                { icon: AlertCircle, text: "Report #R045 pending review", time: "4 hours ago", color: "text-orange-600" },
                { icon: Users, text: "New patient registered", time: "6 hours ago", color: "text-blue-600" },
                { icon: Activity, text: "System backup completed", time: "1 day ago", color: "text-purple-600" },
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 pb-3 border-b last:border-0">
                  <item.icon className={`w-5 h-5 ${item.color}`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{item.text}</p>
                    <p className="text-xs text-gray-500">{item.time}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
