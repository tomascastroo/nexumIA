import React from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, Users } from 'lucide-react';

interface AdvancedChartsProps {
  debtors: any[];
  timeRange?: string;
}

const AdvancedCharts: React.FC<AdvancedChartsProps> = ({ debtors, timeRange = '7d' }) => {
  // Generate time series data for debt trends
  const generateTimeSeriesData = () => {
    const days = 7;
    const data = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      // Simulate debt changes over time
      const baseAmount = 10000;
      const randomChange = (Math.random() - 0.5) * 2000;
      const amount = baseAmount + randomChange;
      
      data.push({
        date: date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' }),
        deuda: Math.round(amount),
        deudores: Math.floor(Math.random() * 50) + 20,
        pagos: Math.floor(Math.random() * 5000) + 1000
      });
    }
    
    return data;
  };

  // Generate debt distribution by ranges
  const generateDebtRanges = () => {
    const ranges = [
      { name: '0-1K', min: 0, max: 1000, color: '#10B981' },
      { name: '1K-5K', min: 1000, max: 5000, color: '#3B82F6' },
      { name: '5K-10K', min: 5000, max: 10000, color: '#F59E0B' },
      { name: '10K-25K', min: 10000, max: 25000, color: '#EF4444' },
      { name: '25K+', min: 25000, max: Infinity, color: '#8B5CF6' }
    ];

    return ranges.map(range => {
      const count = debtors.filter(d => {
        const debt = parseFloat(d.custom_data?.deuda || '0');
        return debt >= range.min && debt < range.max;
      }).length;
      
      return {
        name: range.name,
        value: count,
        color: range.color
      };
    });
  };

  // Generate payment success rate by state
  const generatePaymentSuccessData = () => {
    const states = ['ACTIVO', 'PENDIENTE', 'PAGADO', 'GRIS', 'RECHAZADO'];
    return states.map(state => {
      const stateDebtors = debtors.filter(d => d.state === state);
      const total = stateDebtors.length;
      const paid = stateDebtors.filter(d => d.state === 'PAGADO').length;
      const successRate = total > 0 ? (paid / total) * 100 : 0;
      
      return {
        state,
        successRate: Math.round(successRate),
        total,
        paid
      };
    });
  };

  const timeSeriesData = generateTimeSeriesData();
  const debtRangesData = generateDebtRanges();
  const paymentSuccessData = generatePaymentSuccessData();

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-8">
      {/* Time Series Chart */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Tendencia de Deuda</h3>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-600" />
            <span className="text-sm text-gray-600">Últimos 7 días</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeSeriesData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => [
                name === 'deuda' ? `$${value.toLocaleString()}` : value,
                name === 'deuda' ? 'Deuda Total' : name === 'deudores' ? 'Deudores' : 'Pagos'
              ]}
            />
            <Area 
              type="monotone" 
              dataKey="deuda" 
              stackId="1" 
              stroke="#3B82F6" 
              fill="#3B82F6" 
              fillOpacity={0.6}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Debt Distribution and Payment Success */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Debt Distribution by Ranges */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Distribución por Rango de Deuda</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={debtRangesData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {debtRangesData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Payment Success Rate */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tasa de Éxito por Estado</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={paymentSuccessData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="state" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}%`, 'Tasa de Éxito']} />
              <Bar dataKey="successRate" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Deuda Promedio</p>
              <p className="text-2xl font-bold text-gray-900">
                ${(debtors.reduce((sum, d) => sum + parseFloat(d.custom_data?.deuda || '0'), 0) / Math.max(debtors.length, 1)).toLocaleString()}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-600" />
          </div>
          <div className="mt-2 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <span className="text-green-600">+12.5%</span>
            <span className="text-gray-600 ml-1">vs mes anterior</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Deudores Activos</p>
              <p className="text-2xl font-bold text-gray-900">
                {debtors.filter(d => d.state === 'ACTIVO').length}
              </p>
            </div>
            <Users className="w-8 h-8 text-green-600" />
          </div>
          <div className="mt-2 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <span className="text-green-600">+8.2%</span>
            <span className="text-gray-600 ml-1">vs mes anterior</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tasa de Respuesta</p>
              <p className="text-2xl font-bold text-gray-900">
                {debtors.length > 0 ? Math.round((debtors.filter(d => d.state !== 'GRIS').length / debtors.length) * 100) : 0}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-600" />
          </div>
          <div className="mt-2 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <span className="text-green-600">+5.3%</span>
            <span className="text-gray-600 ml-1">vs mes anterior</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pagos Recolectados</p>
              <p className="text-2xl font-bold text-gray-900">
                ${debtors.filter(d => d.state === 'PAGADO').reduce((sum, d) => sum + parseFloat(d.custom_data?.deuda || '0'), 0).toLocaleString()}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-600" />
          </div>
          <div className="mt-2 flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <span className="text-green-600">+15.7%</span>
            <span className="text-gray-600 ml-1">vs mes anterior</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedCharts; 