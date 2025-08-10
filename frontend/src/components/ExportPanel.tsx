import React, { useState } from 'react';
import { Download, FileText, BarChart3, Calendar, Filter } from 'lucide-react';

interface ExportPanelProps {
  debtors: any[];
  onExport: (format: string, filters: any) => void;
}

const ExportPanel: React.FC<ExportPanelProps> = ({ debtors, onExport }) => {
  const [showPanel, setShowPanel] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');
  const [dateRange, setDateRange] = useState('all');
  const [includeFilters, setIncludeFilters] = useState(false);

  const handleExport = () => {
    const filters = {
      format: exportFormat,
      dateRange,
      includeFilters
    };
    onExport(exportFormat, filters);
    setShowPanel(false);
  };

  const getExportStats = () => {
    const total = debtors.length;
    const active = debtors.filter(d => d.state === 'ACTIVO').length;
    const pending = debtors.filter(d => d.state === 'PENDIENTE').length;
    const paid = debtors.filter(d => d.state === 'PAGADO').length;
    const totalDebt = debtors.reduce((sum, d) => sum + parseFloat(d.custom_data?.deuda || '0'), 0);

    return { total, active, pending, paid, totalDebt };
  };

  const stats = getExportStats();

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Exportar Datos</h3>
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Download className="w-4 h-4" />
            Exportar
          </button>
        </div>

        {/* Export Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.active}</div>
            <div className="text-sm text-gray-600">Activos</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            <div className="text-sm text-gray-600">Pendientes</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats.paid}</div>
            <div className="text-sm text-gray-600">Pagados</div>
          </div>
        </div>

        {/* Export Options */}
        {showPanel && (
          <div className="border-t border-gray-200 pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Formato de Exportación
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="format"
                      value="csv"
                      checked={exportFormat === 'csv'}
                      onChange={(e) => setExportFormat(e.target.value)}
                      className="mr-2"
                    />
                    <FileText className="w-4 h-4 mr-2 text-gray-600" />
                    CSV
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="format"
                      value="excel"
                      checked={exportFormat === 'excel'}
                      onChange={(e) => setExportFormat(e.target.value)}
                      className="mr-2"
                    />
                    <BarChart3 className="w-4 h-4 mr-2 text-gray-600" />
                    Excel
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="format"
                      value="pdf"
                      checked={exportFormat === 'pdf'}
                      onChange={(e) => setExportFormat(e.target.value)}
                      className="mr-2"
                    />
                    <FileText className="w-4 h-4 mr-2 text-gray-600" />
                    PDF
                  </label>
                </div>
              </div>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rango de Fechas
                </label>
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">Todos los registros</option>
                  <option value="today">Hoy</option>
                  <option value="week">Última semana</option>
                  <option value="month">Último mes</option>
                  <option value="quarter">Último trimestre</option>
                </select>
              </div>

              {/* Additional Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Opciones Adicionales
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={includeFilters}
                      onChange={(e) => setIncludeFilters(e.target.checked)}
                      className="mr-2"
                    />
                    <Filter className="w-4 h-4 mr-2 text-gray-600" />
                    Incluir filtros aplicados
                  </label>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowPanel(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Exportar {exportFormat.toUpperCase()}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportPanel; 