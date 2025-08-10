import React, { useEffect, useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { 
  Search, Filter, Download, Plus, Eye, Edit, Trash2, 
  TrendingUp, Users, DollarSign, AlertTriangle, CheckCircle,
  Phone, Mail, Calendar, MapPin
} from 'lucide-react';
import { fetchDebtors, Debtor, DebtorFilters, DebtorSort } from '../services/debtorService';
import { getDebtorDatasets, DebtorDataset } from '../services/debtorDatasetService';
import AdvancedCharts from '../components/AdvancedCharts';
import ExportPanel from '../components/ExportPanel';
import AlertPanel from '../components/AlertPanel';

interface DashboardStats {
  totalDebtors: number;
  activeDebtors: number;
  pendingPayments: number;
  totalDebt: number;
  averageDebt: number;
  responseRate: number;
}

interface ChartData {
  name: string;
  value: number;
  color?: string;
}

const Dashboard: React.FC = () => {
  const [debtors, setDebtors] = useState<Debtor[]>([]);
  const [datasets, setDatasets] = useState<DebtorDataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<DebtorFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState<DashboardStats>({
    totalDebtors: 0,
    activeDebtors: 0,
    pendingPayments: 0,
    totalDebt: 0,
    averageDebt: 0,
    responseRate: 0
  });

  // Load datasets on component mount
  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const data = await getDebtorDatasets();
        setDatasets(data);
        if (data.length > 0) {
          setSelectedDatasetId(data[0].id);
        }
      } catch (err: any) {
        setError(err.message);
      }
    };
    loadDatasets();
  }, []);

  // Load debtors when dataset changes
  useEffect(() => {
    if (selectedDatasetId) {
      loadDebtors();
    }
  }, [selectedDatasetId, filters]);

  const loadDebtors = async () => {
    if (!selectedDatasetId) return;
    
    setLoading(true);
    try {
      const data = await fetchDebtors(selectedDatasetId, filters);
      setDebtors(data);
      calculateStats(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (debtorsData: Debtor[]) => {
    const total = debtorsData.length;
    const active = debtorsData.filter(d => d.state === 'ACTIVO').length;
    const pending = debtorsData.filter(d => d.state === 'PENDIENTE').length;
    
    // Calculate debt amounts from custom_data
    const debtAmounts = debtorsData
      .map(d => parseFloat(d.custom_data?.deuda || '0'))
      .filter(amount => !isNaN(amount));
    
    const totalDebt = debtAmounts.reduce((sum, amount) => sum + amount, 0);
    const averageDebt = debtAmounts.length > 0 ? totalDebt / debtAmounts.length : 0;
    
    // Calculate response rate (debtors who have responded)
    const responded = debtorsData.filter(d => 
      d.state === 'ACTIVO' || d.state === 'PENDIENTE' || d.state === 'PAGADO'
    ).length;
    const responseRate = total > 0 ? (responded / total) * 100 : 0;

    setStats({
      totalDebtors: total,
      activeDebtors: active,
      pendingPayments: pending,
      totalDebt,
      averageDebt,
      responseRate
    });
  };

  const getStateColor = (state: string) => {
    switch (state.toUpperCase()) {
      case 'ACTIVO': return 'bg-green-100 text-green-800';
      case 'PENDIENTE': return 'bg-yellow-100 text-yellow-800';
      case 'PAGADO': return 'bg-blue-100 text-blue-800';
      case 'GRIS': return 'bg-gray-100 text-gray-800';
      case 'RECHAZADO': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state.toUpperCase()) {
      case 'ACTIVO': return <CheckCircle className="w-4 h-4" />;
      case 'PENDIENTE': return <AlertTriangle className="w-4 h-4" />;
      case 'PAGADO': return <TrendingUp className="w-4 h-4" />;
      case 'GRIS': return <Users className="w-4 h-4" />;
      case 'RECHAZADO': return <Trash2 className="w-4 h-4" />;
      default: return <Users className="w-4 h-4" />;
    }
  };

  // Chart data preparation
  const stateDistributionData: ChartData[] = [
    { name: 'Activo', value: debtors.filter(d => d.state === 'ACTIVO').length, color: '#10B981' },
    { name: 'Pendiente', value: debtors.filter(d => d.state === 'PENDIENTE').length, color: '#F59E0B' },
    { name: 'Pagado', value: debtors.filter(d => d.state === 'PAGADO').length, color: '#3B82F6' },
    { name: 'Gris', value: debtors.filter(d => d.state === 'GRIS').length, color: '#6B7280' },
    { name: 'Rechazado', value: debtors.filter(d => d.state === 'RECHAZADO').length, color: '#EF4444' }
  ];

  const debtAmountData = debtors
    .filter(d => d.custom_data?.deuda)
    .map(d => ({
      name: d.phone.slice(-4),
      deuda: parseFloat(d.custom_data.deuda) || 0,
      state: d.state
    }))
    .sort((a, b) => b.deuda - a.deuda)
    .slice(0, 10);

  const filteredDebtors = debtors.filter(debtor =>
    debtor.phone.toLowerCase().includes(searchTerm.toLowerCase()) ||
    debtor.state.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (debtor.custom_data?.nombre && 
     debtor.custom_data.nombre.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const handleExport = (format: string, filters: any) => {
    console.log('Exporting data:', { format, filters, debtors });
    // Here you would implement the actual export functionality
    alert(`Exportando datos en formato ${format.toUpperCase()}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard de Gestión de Deudores</h1>
          <p className="mt-2 text-gray-600">Monitoreo y análisis de cartera de deudores</p>
        </div>

        {/* Dataset Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seleccionar Dataset
          </label>
          <select
            value={selectedDatasetId || ''}
            onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
            className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {datasets.map(dataset => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name}
              </option>
            ))}
          </select>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Deudores</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalDebtors}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Activos</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeDebtors}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pendientes</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pendingPayments}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <DollarSign className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Deuda Total</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${stats.totalDebt.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* State Distribution Pie Chart */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Distribución por Estado</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={stateDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {stateDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Debt Amount Bar Chart */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 10 Deudas</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={debtAmountData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value}`, 'Deuda']} />
                <Bar dataKey="deuda" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Advanced Charts */}
        <AdvancedCharts debtors={debtors} />

        {/* Alert Panel */}
        <AlertPanel debtors={debtors} />

        {/* Export Panel */}
        <ExportPanel debtors={debtors} onExport={handleExport} />

        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 mb-6">
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Buscar deudores..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Filter className="w-4 h-4" />
                Filtros
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Plus className="w-4 h-4" />
                Nuevo Deudor
              </button>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select
                    value={filters.state || ''}
                    onChange={(e) => setFilters({...filters, state: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Todos los estados</option>
                    <option value="ACTIVO">Activo</option>
                    <option value="PENDIENTE">Pendiente</option>
                    <option value="PAGADO">Pagado</option>
                    <option value="GRIS">Gris</option>
                    <option value="RECHAZADO">Rechazado</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Deuda Mínima</label>
                  <input
                    type="number"
                    placeholder="0"
                    value={filters.min_amount || ''}
                    onChange={(e) => setFilters({...filters, min_amount: Number(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Deuda Máxima</label>
                  <input
                    type="number"
                    placeholder="999999"
                    value={filters.max_amount || ''}
                    onChange={(e) => setFilters({...filters, max_amount: Number(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Debtors Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Lista de Deudores</h3>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Cargando deudores...</p>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <p className="text-red-600">{error}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Teléfono
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nombre
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Deuda
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredDebtors.map((debtor) => (
                    <tr key={debtor.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Phone className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm font-medium text-gray-900">{debtor.phone}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">
                          {debtor.custom_data?.nombre || 'Sin nombre'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStateColor(debtor.state)}`}>
                          {getStateIcon(debtor.state)}
                          <span className="ml-1">{debtor.state}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">
                          ${parseFloat(debtor.custom_data?.deuda || '0').toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button className="text-blue-600 hover:text-blue-900">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="text-green-600 hover:text-green-900">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="text-red-600 hover:text-red-900">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {filteredDebtors.length === 0 && (
                <div className="p-8 text-center">
                  <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No se encontraron deudores</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 