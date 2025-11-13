"""
Batch CSV Processor for Package Emissions Calculator - OPTIMIZED VERSION

Key improvements:
- Concurrent processing using ThreadPoolExecutor
- Removed mandatory 1s delay between calls
- Progress bar shows actual progress
- Reduced console output during processing
- Optional rate limiting instead of fixed delays
"""

import pandas as pd
import time
from typing import Dict, Optional, List
from datetime import datetime
from emissions_calculator import calculate_package_emissions, EmissionResult, print_emissions_report
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


class BatchEmissionsProcessor:
    """Process multiple packages from CSV and calculate emissions"""
    
    def __init__(self, credentials: Dict[str, Dict[str, str]]):
        """
        Initialize batch processor with carrier credentials.
        
        Args:
            credentials: Dict of carrier credentials
                {
                    'ups': {'client_id': '...', 'client_secret': '...'},
                    'fedex': {'client_id': '...', 'client_secret': '...'},
                    'usps': {'client_id': '...', 'client_secret': '...'},
                    'dhl': {'client_id': '...', 'client_secret': '...'}
                }
        """
        self.credentials = credentials
        self.results = []
        self.errors = []
        self.lock = Lock()  # For thread-safe access to shared lists
        
    def process_csv(self, 
                   input_file: str, 
                   output_file: str = None,
                   delay_seconds: float = 0.0,
                   production: bool = False,
                   carrier_column: str = 'carrier',
                   tracking_column: str = 'tracking_number',
                   max_workers: int = 10,
                   verbose: bool = False) -> pd.DataFrame:
        """
        Process a CSV file with tracking numbers and calculate emissions.
        
        Expected CSV columns (flexible):
            - tracking_number or Tracking Number (required): Package tracking number
            - carrier or Item (required): Carrier name (ups, fedex, usps, dhl)
            - length_cm, width_cm, height_cm (optional): Package dimensions
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (default: input_file + '_emissions.csv')
            delay_seconds: Delay between API calls to avoid rate limiting (default: 0)
            production: Use production environment (default: False for testing)
            carrier_column: Name of the carrier column (default: 'carrier')
            tracking_column: Name of the tracking number column (default: 'tracking_number')
            max_workers: Number of concurrent threads (default: 10)
            verbose: Show detailed progress for each package (default: False)
        
        Returns:
            DataFrame with results
        """
        print(f"\n{'='*80}")
        print(f"🌱 WPI Greenboard - Batch Emissions Processor (OPTIMIZED)")
        print(f"{'='*80}\n")
        
        # Read input CSV
        from tqdm import tqdm
        try:
            df = pd.read_csv(input_file)
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            print(f"✅ Loaded {len(df)} packages from {input_file}")
            print(f"   Columns found: {list(df.columns)[:5]}..." if len(df.columns) > 5 else f"   Columns: {list(df.columns)}")
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return None
        
        # Auto-detect column names (case-insensitive, flexible)
        tracking_col = self._find_column(df, [tracking_column, 'Tracking Number', 'tracking_number', 'TrackingNumber', 'Tracking #'])
        carrier_col = self._find_column(df, [carrier_column, 'Item', 'carrier', 'Carrier', 'Service'])
        
        if not tracking_col:
            print(f"❌ Could not find tracking number column")
            print(f"   Looking for: {tracking_column}, 'Tracking Number', 'tracking_number'")
            print(f"   Available columns: {list(df.columns)}")
            return None
        
        if not carrier_col:
            print(f"❌ Could not find carrier column")
            print(f"   Looking for: {carrier_column}, 'Item', 'carrier'")
            print(f"   Available columns: {list(df.columns)}")
            return None
        
        print(f"✅ Using tracking column: '{tracking_col}'")
        print(f"✅ Using carrier column: '{carrier_col}'")
        
        # Standardize column names for processing
        df['_tracking_number'] = df[tracking_col]
        df['_carrier'] = df[carrier_col]
        
        print(f"✅ CSV validation passed")
        
        # Show carrier distribution
        carrier_counts = df['_carrier'].value_counts()
        print(f"\n📊 Carrier Distribution:")
        for carrier, count in carrier_counts.items():
            status = "✅" if carrier.lower() in self.credentials else "⚠️ "
            print(f"   {status} {carrier}: {count} packages")
        
        print(f"\n🚀 Processing {len(df)} packages with {max_workers} concurrent workers...")
        if delay_seconds > 0:
            print(f"⏱️  Rate limiting: {delay_seconds}s delay between requests")
        else:
            print(f"⚡ No rate limiting - maximum speed")
        print(f"{'─'*80}\n")
        
        # Process with concurrent threads
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {}
            for idx, row in df.iterrows():
                future = executor.submit(
                    self._process_single_package_wrapper,
                    idx, row, production, verbose, delay_seconds, len(df)
                )
                futures[future] = idx
            
            # Process completed tasks with progress bar
            with tqdm(total=len(df), desc="Processing", unit="pkg") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    with self.lock:
                        self.results.append(result)
                    pbar.update(1)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Processing completed in {elapsed_time:.2f}s ({len(df)/elapsed_time:.2f} packages/sec)")
        
        # Sort results by original index to maintain order
        self.results.sort(key=lambda x: x.get('_index', 0))
        
        # Convert results to DataFrame
        results_df = self._create_results_dataframe(df)
        
        # Save to output file
        if output_file is None:
            output_file = input_file.replace('.csv', '_emissions.csv')
        
        try:
            results_df.to_csv(output_file, index=False)
            print(f"\n{'='*80}")
            print(f"✅ Results saved to: {output_file}")
            print(f"{'='*80}\n")
        except Exception as e:
            print(f"\n❌ Error saving results: {e}")
        
        # Print summary
        self._print_summary(elapsed_time)
        
        return results_df
    
    def _process_single_package_wrapper(self, idx: int, row: pd.Series, 
                                       production: bool, verbose: bool,
                                       delay_seconds: float, total: int) -> Dict:
        """
        Wrapper for processing a single package with optional rate limiting.
        """
        # Optional rate limiting
        if delay_seconds > 0:
            time.sleep(delay_seconds * idx / total)  # Stagger requests
        
        result = self._process_single_package(row, production, verbose, idx, total)
        result['_index'] = idx  # Preserve original order
        return result
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """
        Find a column by trying multiple possible names (case-insensitive).
        
        Args:
            df: DataFrame to search
            possible_names: List of possible column names
        
        Returns:
            Actual column name if found, None otherwise
        """
        df_columns_lower = {col.lower(): col for col in df.columns}
        
        for name in possible_names:
            if name.lower() in df_columns_lower:
                return df_columns_lower[name.lower()]
        
        return None
    
    def _process_single_package(self, row: pd.Series, production: bool,
                               verbose: bool = False, idx: int = 0, 
                               total: int = 0) -> Dict:
        """
        Process a single package and return result dictionary.
        
        Args:
            row: DataFrame row with package information
            production: Use production environment
            verbose: Print detailed progress
            idx: Index for progress tracking
            total: Total packages for progress tracking
        
        Returns:
            Dict with results or error information
        """
        tracking_number = str(row['_tracking_number']).strip().rstrip('_')
        carrier = str(row['_carrier']).strip().lower()
        
        # Map common carrier names
        carrier_map = {
            'usps': 'usps',
            'ups': 'ups',
            'fedex': 'fedex',
            'dhl': 'dhl',
            'amazon': 'amazon',
            'lasership': 'lasership',
        }
        
        carrier = carrier_map.get(carrier, carrier)
        
        # Check if carrier is supported
        if carrier not in self.credentials:
            if carrier in ['amazon', 'lasership']:
                error_msg = f"Carrier '{carrier}' not supported (no public tracking API)"
            else:
                error_msg = f"Carrier '{carrier}' not configured"
            
            with self.lock:
                self.errors.append({
                    'tracking_number': tracking_number,
                    'carrier': carrier,
                    'error': error_msg
                })
            
            return {
                'tracking_number': tracking_number,
                'carrier': carrier,
                'status': 'unsupported',
                'error_message': error_msg
            }
        
        # Extract dimensions if provided
        dimensions = None
        if all(col in row for col in ['length_cm', 'width_cm', 'height_cm']):
            if pd.notna(row['length_cm']) and pd.notna(row['width_cm']) and pd.notna(row['height_cm']):
                dimensions = (
                    float(row['length_cm']),
                    float(row['width_cm']),
                    float(row['height_cm'])
                )
        
        try:
            # Calculate emissions
            result = calculate_package_emissions(
                carrier=carrier,
                tracking_number=tracking_number,
                credentials=self.credentials[carrier],
                dimensions=dimensions,
                production=production
            )
            
            if result:
                if verbose:
                    print(f"   ✅ Success: {result.total_emissions_kg:.4f} kg CO2e")
                return self._emission_result_to_dict(result)
            else:
                error_msg = "Calculation failed"
                if verbose:
                    print(f"   ❌ {error_msg}")
                
                with self.lock:
                    self.errors.append({
                        'tracking_number': tracking_number,
                        'carrier': carrier,
                        'error': error_msg
                    })
                
                return {
                    'tracking_number': tracking_number,
                    'carrier': carrier,
                    'status': 'error',
                    'error_message': error_msg
                }
        
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            if verbose:
                print(f"   ❌ {error_msg}")
            
            with self.lock:
                self.errors.append({
                    'tracking_number': tracking_number,
                    'carrier': carrier,
                    'error': error_msg
                })
            
            return {
                'tracking_number': tracking_number,
                'carrier': carrier,
                'status': 'error',
                'error_message': error_msg
            }
    
    def _emission_result_to_dict(self, result: EmissionResult) -> Dict:
        """Convert EmissionResult to a flat dictionary for CSV export"""
        pkg = result.package_info
        
        # Calculate environmental equivalents
        trees_needed = result.total_emissions_kg / 21
        miles_driven = result.total_emissions_kg / 0.404
        
        return {
            'tracking_number': pkg.tracking_number,
            'carrier': pkg.carrier,
            'status': 'success',
            'service': pkg.service_description,
            'service_code': pkg.service_code,
            
            # Weight
            'weight_kg': round(result.weight_used_kg, 3),
            'weight_lbs': round(result.weight_used_kg * 2.20462, 3),
            'is_dimensional_weight': result.is_dimensional,
            
            # Route
            'origin_city': pkg.origin.city if pkg.origin else None,
            'origin_state': pkg.origin.state if pkg.origin else None,
            'origin_country': pkg.origin.country if pkg.origin else None,
            'destination_city': pkg.destination.city if pkg.destination else None,
            'destination_state': pkg.destination.state if pkg.destination else None,
            'destination_country': pkg.destination.country if pkg.destination else None,
            'distance_km': round(result.distance_km, 2),
            'distance_miles': round(result.distance_km * 0.621371, 2),
            
            # Emissions
            'transport_mode': result.transport_mode,
            'emission_factor': round(result.emission_factor, 4),
            'total_emissions_kg_co2e': round(result.total_emissions_kg, 4),
            'main_transit_emissions_kg': round(result.breakdown[0]['emissions_kg'], 4) if result.breakdown else 0,
            'last_mile_emissions_kg': round(result.breakdown[1]['emissions_kg'], 4) if len(result.breakdown) > 1 else 0,
            
            # Environmental context
            'trees_needed_1_year': round(trees_needed, 2),
            'equivalent_miles_driven': round(miles_driven, 1),
            
            'error_message': None
        }
    
    def _create_results_dataframe(self, original_df: pd.DataFrame) -> pd.DataFrame:
        """Create a DataFrame from results"""
        results_df = pd.DataFrame(self.results)
        
        # Remove internal tracking column
        if '_index' in results_df.columns:
            results_df = results_df.drop(columns=['_index'])
        
        # Merge with original data to preserve any additional columns
        if 'tracking_number' in original_df.columns:
            results_df = original_df.merge(
                results_df,
                on='tracking_number',
                how='left',
                suffixes=('_original', '')
            )
        
        return results_df
    
    def _print_summary(self, elapsed_time: float = None):
        """Print summary statistics"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('status') == 'success')
        failed = total - successful
        
        print(f"\n{'='*80}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"Total Packages: {total}")
        print(f"✅ Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        
        if elapsed_time:
            print(f"⏱️  Processing Time: {elapsed_time:.2f}s")
            print(f"📈 Throughput: {total/elapsed_time:.2f} packages/sec")
        
        if successful > 0:
            total_emissions = sum(
                r.get('total_emissions_kg_co2e', 0) 
                for r in self.results 
                if r.get('status') == 'success'
            )
            avg_emissions = total_emissions / successful
            
            print(f"\n🌍 Total Emissions: {total_emissions:.4f} kg CO2e")
            print(f"📊 Average per Package: {avg_emissions:.4f} kg CO2e")
            print(f"🌳 Trees Needed (1 year): {total_emissions / 21:.2f}")
            print(f"🚗 Equivalent Miles Driven: {total_emissions / 0.404:.1f}")
        
        if self.errors:
            print(f"\n⚠️  Errors encountered:")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"   • {error['tracking_number']} ({error['carrier']}): {error['error']}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more errors")
        
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # Set up credentials for all carriers
    credentials = {
        'ups': {
            'client_id': 'HCTsyp8JsmGuiOYCkxpZAak9ZusNbA8Me9d1k5g7rmivxpoC',
            'client_secret': 'bbUGGCg1q66AuEeGV66EjhcbG6GNtOGYTb1r5vqAxssUaBsovaQIKPiTWHHpAGZV'
        },
        'usps': {
            'client_id': 'vrBISZnb8yn4KTNm0SA0UAA4yqlDfGdEFHkfARJzWgizAzGq',
            'client_secret': '13b8Ius4epIhNbIlz2s9KIlAOT0JVkSqnBGjtD6q5rnW5TRHrchLZYBfwUAaM51Y'
        },
        'fedex': {
            'client_id': 'l74673b0ec87d749268da2b0e59460429c',
            'client_secret': '4e8527a4c6614ef386672eebeb086223'
        },
        'dhl': {
            'client_id': 'JLOAsRhxyRDiU4hyT1w4ueexJlqSMVqg',
            'client_secret': 'cMI8ojXzljz32GhE'
        },
        'amazon': {
            'client_id': None,
            'client_secret': None
        }
    }
    
    # Process the CSV
    processor = BatchEmissionsProcessor(credentials)
    import os
    current_dir = os.getcwd()
    results_df = processor.process_csv(
        input_file=current_dir + '/src/greenboard/emissions/oct_tracking_numbers.csv',
        output_file=current_dir + '/src/greenboard/emissions/oct_tracking_numbers_with_emissions.csv',
        delay_seconds=0.0,  # No delay for maximum speed
        production=True,
        max_workers=10,  # Process 10 packages concurrently
        verbose=False  # Set to True for detailed progress per package
    )
    
    # View results
    if results_df is not None:
        print("\nResults Preview:")
        print(results_df[['tracking_number', 'carrier', 'status', 'total_emissions_kg_co2e']].head())